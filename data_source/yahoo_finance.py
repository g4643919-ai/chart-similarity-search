import yfinance as yf
import pandas as pd
import streamlit as st
from typing import Tuple, Optional, Dict, Any
from config import CACHE_TTL

import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import time
from typing import Tuple, Optional, Dict, Any
from config import CACHE_TTL

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_stock_data(formatted_ticker: str, period: str = "10y") -> Tuple[Optional[pd.DataFrame], Optional[Dict[str, Any]], Optional[str]]:
    """
    Yahoo Finance から株価データおよび銘柄情報を取得する。
    通信障害やレート制限 (HTTP 429) が起きても自動リトライ・フォールバックでアプリを停止させない。
    """
    if not formatted_ticker:
        return None, None, "銘柄コードを入力してください。"
        
    df = None
    info_dict = None
    last_error = None
    
    # 複数回のリトライ処理 (レート制限・通信一時エラー対策)
    for attempt in range(3):
        try:
            ticker_obj = yf.Ticker(formatted_ticker)
            df = ticker_obj.history(period=period, auto_adjust=True)
            
            if df is not None and not df.empty:
                # 銘柄基本情報の安全な取得 (info 取得エラーでクラッシュしない保護)
                try:
                    raw_info = ticker_obj.info
                    if isinstance(raw_info, dict) and raw_info:
                        info_dict = {
                            'shortName': raw_info.get('shortName') or raw_info.get('longName') or formatted_ticker,
                            'longName': raw_info.get('longName') or formatted_ticker,
                            'currency': raw_info.get('currency', 'JPY' if formatted_ticker.endswith('.T') else 'USD'),
                            'previousClose': raw_info.get('previousClose'),
                            'fiftyTwoWeekHigh': raw_info.get('fiftyTwoWeekHigh'),
                            'fiftyTwoWeekLow': raw_info.get('fiftyTwoWeekLow'),
                        }
                except Exception:
                    pass
                break
        except Exception as e:
            last_error = str(e)
            time.sleep(0.5 * (attempt + 1))
            
    if df is None or df.empty:
        return None, None, f"銘柄 '{formatted_ticker}' の株価データを取得できませんでした。時間をおいて再試行してください。（エラー: {last_error or 'データ応答なし'}）"
        
    try:
        # インデックスが DatetimeIndex でない場合の対応
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
            
        # タイムゾーンの削除（比較しやすくするため）
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
            
        # 重複日付の削除・昇順ソート
        df = df[~df.index.duplicated(keep='first')]
        df = df.sort_index(ascending=True)
        
        # 欠損値処理
        df = df.dropna(subset=['Close'])
        
        if len(df) < 40:
            return None, None, "分析に必要な過去データ（最低40営業日）が不足しています。"
            
        if not info_dict:
            info_dict = {
                'shortName': formatted_ticker,
                'longName': formatted_ticker,
                'currency': 'JPY' if formatted_ticker.endswith('.T') else 'USD',
                'fiftyTwoWeekHigh': float(df['High'].max()),
                'fiftyTwoWeekLow': float(df['Low'].min()),
            }
            
        return df, info_dict, None

    except Exception as e:
        return None, None, f"株価データの解析処理中にエラーが発生しました: {str(e)}"

