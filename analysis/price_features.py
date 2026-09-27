import pandas as pd
import numpy as np
from typing import Dict, Any

def normalize_prices(df: pd.DataFrame) -> pd.DataFrame:
    """
    チャートデータの開始日の Close 価格を 100 として正規化する。
    """
    df_norm = df.copy()
    base_price = df_norm['Close'].iloc[0]
    if base_price == 0:
        base_price = 1.0
        
    df_norm['Norm_Open'] = (df_norm['Open'] / base_price) * 100
    df_norm['Norm_High'] = (df_norm['High'] / base_price) * 100
    df_norm['Norm_Low'] = (df_norm['Low'] / base_price) * 100
    df_norm['Norm_Close'] = (df_norm['Close'] / base_price) * 100
    return df_norm

def extract_price_features(df: pd.DataFrame, window: int = 40) -> Dict[str, Any]:
    """
    直近 window 営業日における価格変化・高値安値の特徴量を計算する。
    """
    sub_df = df.tail(window).copy()
    close_series = sub_df['Close']
    n = len(close_series)
    
    features = {}
    
    # 騰落率 (各営業日前の終値と比較)
    features['return_1d'] = ((close_series.iloc[-1] / close_series.iloc[-2]) - 1) * 100 if n >= 2 else 0.0
    features['return_3d'] = ((close_series.iloc[-1] / close_series.iloc[-4]) - 1) * 100 if n >= 4 else 0.0
    features['return_5d'] = ((close_series.iloc[-1] / close_series.iloc[-6]) - 1) * 100 if n >= 6 else 0.0
    features['return_10d'] = ((close_series.iloc[-1] / close_series.iloc[-11]) - 1) * 100 if n >= 11 else 0.0
    features['return_20d'] = ((close_series.iloc[-1] / close_series.iloc[-21]) - 1) * 100 if n >= 21 else 0.0
    features['return_window'] = ((close_series.iloc[-1] / close_series.iloc[0]) - 1) * 100 if n >= 1 else 0.0
    
    # 高値・安値
    sub_high = sub_df['High']
    sub_low = sub_df['Low']
    
    features['high_window'] = sub_high.max()
    features['low_window'] = sub_low.min()
    
    # 直近20営業日高値・安値
    sub_20 = sub_df.tail(min(20, n))
    features['high_20d'] = sub_20['High'].max()
    features['low_20d'] = sub_20['Low'].min()
    
    # 直近高値からの下落率 & 安値からの反発率
    latest_close = close_series.iloc[-1]
    features['drawdown_from_high'] = ((latest_close - features['high_window']) / features['high_window']) * 100
    features['rebound_from_low'] = ((latest_close - features['low_window']) / features['low_window']) * 100
    
    # 現在のレンジ位置 (0.0 ～ 1.0)
    denom = features['high_window'] - features['low_window']
    features['range_position'] = (latest_close - features['low_window']) / denom if denom != 0 else 0.5
    
    return features
