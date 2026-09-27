import pandas as pd
import numpy as np
from typing import Dict, Any
from ui.charts import calc_moving_averages

def extract_trend_features(df: pd.DataFrame, window: int = 40) -> Dict[str, Any]:
    """
    移動平均線（5/25/75MA）との関係、傾き、および高値・安値構造（HH, HL, LH, LL）を解析する。
    """
    df_ma = calc_moving_averages(df)
    sub_df = df_ma.tail(window).copy()
    
    latest = sub_df.iloc[-1]
    close_p = latest['Close']
    
    ma5 = latest['5MA']
    ma25 = latest['25MA']
    ma75 = latest['75MA']
    
    # MA乖離率 (%)
    dev_25ma = ((close_p - ma25) / ma25 * 100) if pd.notna(ma25) and ma25 != 0 else 0.0
    dev_75ma = ((close_p - ma75) / ma75 * 100) if pd.notna(ma75) and ma75 != 0 else 0.0
    
    # 位置関係
    is_above_25ma = close_p > ma25 if pd.notna(ma25) else False
    is_above_75ma = close_p > ma75 if pd.notna(ma75) else False
    is_25ma_above_75ma = ma25 > ma75 if (pd.notna(ma25) and pd.notna(ma75)) else False
    
    # 傾き (直近5営業日の変化率)
    slope_25ma = 0.0
    if len(sub_df) >= 5 and pd.notna(sub_df['25MA'].iloc[-5]) and sub_df['25MA'].iloc[-5] != 0:
        slope_25ma = ((sub_df['25MA'].iloc[-1] - sub_df['25MA'].iloc[-5]) / sub_df['25MA'].iloc[-5]) * 100
        
    slope_75ma = 0.0
    if len(sub_df) >= 5 and pd.notna(sub_df['75MA'].iloc[-5]) and sub_df['75MA'].iloc[-5] != 0:
        slope_75ma = ((sub_df['75MA'].iloc[-1] - sub_df['75MA'].iloc[-5]) / sub_df['75MA'].iloc[-5]) * 100
        
    # 高値・安値構造 (HH, HL, LH, LL の検出)
    # window期間を前半と後半に分けてそれぞれの安値・高値を比較
    half = window // 2
    first_half = sub_df.iloc[:half]
    second_half = sub_df.iloc[half:]
    
    first_low = first_half['Low'].min()
    second_low = second_half['Low'].min()
    first_high = first_half['High'].max()
    second_high = second_half['High'].max()
    
    is_higher_low = second_low > first_low    # HL: 安値切り上げ
    is_higher_high = second_high > first_high  # HH: 高値更新
    is_lower_high = second_high < first_high   # LH: 高値切り下げ
    is_lower_low = second_low < first_low     # LL: 安値切り下げ
    
    trend_structure = "レンジ"
    if is_higher_low and is_higher_high:
        trend_structure = "上昇トレンド (HH+HL)"
    elif is_higher_low and not is_higher_high:
        trend_structure = "安値切り上げ (HL)"
    elif is_lower_low and is_lower_high:
        trend_structure = "下落トレンド (LH+LL)"
    elif is_lower_high and not is_lower_low:
        trend_structure = "高値切り下げ (LH)"

    features = {
        'dev_25ma': dev_25ma,
        'dev_75ma': dev_75ma,
        'is_above_25ma': is_above_25ma,
        'is_above_75ma': is_above_75ma,
        'is_25ma_above_75ma': is_25ma_above_75ma,
        'slope_25ma': slope_25ma,
        'slope_75ma': slope_75ma,
        'is_higher_low': is_higher_low,
        'is_higher_high': is_higher_high,
        'is_lower_high': is_lower_high,
        'is_lower_low': is_lower_low,
        'trend_structure': trend_structure
    }
    return features
