import yfinance as yf
import pandas as pd
import streamlit as st
from typing import Tuple, Optional, Dict, Any
from config import CACHE_TTL

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_stock_data(formatted_ticker: str, period: str = "10y") -> Tuple[Optional[pd.DataFrame], Optional[Dict[str, Any]], Optional[str]]:
    """
    Yahoo Finance から株価データおよび銘柄情報を取得する。
    
    Returns:
        (df, info, error_message)
    """
    if not formatted_ticker:
        return None, None, "銘柄コードを入力してください。"
        
    try:
        ticker_obj = yf.Ticker(formatted_ticker)
        # 株価履歴データを取得 (auto_adjust=True で株式分割等を考慮)
        df = ticker_obj.history(period=period, auto_adjust=True)
        
        if df.empty:
            return None, None, f"銘柄 '{formatted_ticker}' の株価データを取得できませんでした。銘柄コードを確認してください。"
            
        # インデックスが DatetimeIndex でない場合の対応
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
            
        # タイムゾーンの削除（比較しやすくするため）
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
            
        # 重複日付の削除・昇順ソート
        df = df[~df.index.duplicated(keep='first')]
        df = df.sort_index(ascending=True)
        
        # 必要なカラムの確認
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            return None, None, f"データに必要なカラム ({', '.join(missing_cols)}) が不足しています。"
            
        # 欠損値処理（前日終値補間など、勝手に作成しない）
        df = df.dropna(subset=['Close'])
        
        if len(df) < 40:
            return None, None, "分析に必要な過去データ（最低40営業日）が不足しています。"
            
        # 銘柄基本情報の取得（失敗してもデータ取得自体は継続する）
        info_dict = {}
        try:
            raw_info = ticker_obj.info
            if isinstance(raw_info, dict):
                info_dict = {
                    'shortName': raw_info.get('shortName') or raw_info.get('longName') or formatted_ticker,
                    'longName': raw_info.get('longName') or formatted_ticker,
                    'currency': raw_info.get('currency', 'JPY' if formatted_ticker.endswith('.T') else 'USD'),
                    'previousClose': raw_info.get('previousClose'),
                    'fiftyTwoWeekHigh': raw_info.get('fiftyTwoWeekHigh'),
                    'fiftyTwoWeekLow': raw_info.get('fiftyTwoWeekLow'),
                }
        except Exception:
            info_dict = {
                'shortName': formatted_ticker,
                'longName': formatted_ticker,
                'currency': 'JPY' if formatted_ticker.endswith('.T') else 'USD',
            }
            
        return df, info_dict, None

    except Exception as e:
        return None, None, f"株価データの取得中にエラーが発生しました: {str(e)}"
