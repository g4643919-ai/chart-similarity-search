import pandas as pd
import numpy as np
from typing import Dict, Any

def extract_candle_features(df: pd.DataFrame, window: int = 40) -> Dict[str, Any]:
    """
    直近のローソク足構造（実体、上ヒゲ、下ヒゲ比率、代表的パターン）を解析する。
    """
    sub_df = df.tail(window).copy()
    latest = sub_df.iloc[-1]
    prev = sub_df.iloc[-2] if len(sub_df) >= 2 else latest
    
    open_p = latest['Open']
    high_p = latest['High']
    low_p = latest['Low']
    close_p = latest['Close']
    
    total_range = high_p - low_p
    if total_range == 0:
        total_range = 1e-6
        
    body = abs(close_p - open_p)
    is_bullish = close_p >= open_p
    
    if is_bullish:
        upper_shadow = high_p - close_p
        lower_shadow = open_p - low_p
    else:
        upper_shadow = high_p - open_p
        lower_shadow = close_p - low_p
        
    body_ratio = body / total_range
    upper_ratio = upper_shadow / total_range
    lower_ratio = lower_shadow / total_range
    
    # 代表的な形状の識別
    candle_type = "通常"
    if body_ratio < 0.1:
        candle_type = "十字線"
    elif lower_ratio > 0.5 and body_ratio < 0.3:
        candle_type = "下ヒゲ陽線" if is_bullish else "下ヒゲ陰線"
    elif upper_ratio > 0.5 and body_ratio < 0.3:
        candle_type = "上ヒゲ陽線" if is_bullish else "上ヒゲ陰線"
    elif body_ratio > 0.7:
        candle_type = "大陽線" if is_bullish else "大陰線"
        
    # 包み足判定（前日を包み込んでいるか）
    is_engulfing = False
    if len(sub_df) >= 2:
        prev_body_min = min(prev['Open'], prev['Close'])
        prev_body_max = max(prev['Open'], prev['Close'])
        curr_body_min = min(open_p, close_p)
        curr_body_max = max(open_p, close_p)
        if curr_body_min <= prev_body_min and curr_body_max >= prev_body_max and body > abs(prev['Close'] - prev['Open']):
            is_engulfing = True
            
    features = {
        'latest_body_ratio': body_ratio,
        'latest_upper_ratio': upper_ratio,
        'latest_lower_ratio': lower_ratio,
        'is_bullish': is_bullish,
        'candle_type': candle_type,
        'is_engulfing': is_engulfing,
        # 過去 window 日間の下ヒゲ平均比率など
        'avg_lower_shadow_ratio': float(
            ((sub_df['Open'].combine(sub_df['Close'], min) - sub_df['Low']) / 
             (sub_df['High'] - sub_df['Low']).replace(0, 1e-6)).mean()
        )
    }
    return features
