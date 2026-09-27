import pandas as pd
import numpy as np
from typing import Dict, Any

def extract_range_features(df: pd.DataFrame, window: int = 40) -> Dict[str, Any]:
    """
    レンジ幅、ボラティリティ（標準偏差）の変化、最高値・最安値までの距離を解析する。
    """
    sub_df = df.tail(window).copy()
    close_series = sub_df['Close']
    n = len(close_series)
    
    high_val = sub_df['High'].max()
    low_val = sub_df['Low'].min()
    latest_close = close_series.iloc[-1]
    
    range_val = high_val - low_val
    range_ratio = (range_val / latest_close) * 100 if latest_close > 0 else 0.0
    
    # 直近20営業日のレンジ幅比率
    sub_20 = sub_df.tail(min(20, n))
    range_20 = sub_20['High'].max() - sub_20['Low'].min()
    range_ratio_20 = (range_20 / latest_close) * 100 if latest_close > 0 else 0.0
    
    # 高値・安値までの距離 (%)
    dist_to_high = ((high_val - latest_close) / latest_close) * 100 if latest_close > 0 else 0.0
    dist_to_low = ((latest_close - low_val) / latest_close) * 100 if latest_close > 0 else 0.0
    
    # ボラティリティ変化（過去20日標準偏差 vs その前の20日標準偏差）
    volatility_expanding = False
    volatility_contracting = False
    
    if n >= 40:
        std_recent = sub_df['Close'].iloc[-20:].std()
        std_prev = sub_df['Close'].iloc[-40:-20].std()
        if std_prev > 0:
            ratio = std_recent / std_prev
            if ratio >= 1.3:
                volatility_expanding = True
            elif ratio <= 0.7:
                volatility_contracting = True

    features = {
        'range_val': range_val,
        'range_ratio': range_ratio,
        'range_ratio_20': range_ratio_20,
        'dist_to_high': dist_to_high,
        'dist_to_low': dist_to_low,
        'volatility_expanding': volatility_expanding,
        'volatility_contracting': volatility_contracting
    }
    return features
