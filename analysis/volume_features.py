import pandas as pd
import numpy as np
from typing import Dict, Any

def extract_volume_features(df: pd.DataFrame, window: int = 40) -> Dict[str, Any]:
    """
    出来高の平均、比率、および株価動向との相関特徴量を解析する。
    """
    sub_df = df.tail(window).copy()
    vol_series = sub_df['Volume']
    n = len(vol_series)
    
    vol_5d_avg = vol_series.tail(min(5, n)).mean()
    vol_20d_avg = vol_series.tail(min(20, n)).mean()
    vol_window_avg = vol_series.mean()
    
    latest_vol = vol_series.iloc[-1]
    vol_ratio_20d = (latest_vol / vol_20d_avg) if vol_20d_avg > 0 else 1.0
    
    # 出来高急増（20日平均の1.5倍以上）/ 出来高減少（0.6倍以下）
    is_volume_surge = vol_ratio_20d >= 1.5
    is_volume_shrink = vol_ratio_20d <= 0.6
    
    # 価格変動と出来高の関係
    # 直近の株価変化
    prev_close = sub_df['Close'].iloc[-2] if n >= 2 else sub_df['Close'].iloc[-1]
    price_up = sub_df['Close'].iloc[-1] >= prev_close
    
    price_up_vol_up = price_up and (vol_ratio_20d > 1.0)
    price_up_vol_down = price_up and (vol_ratio_20d <= 1.0)
    price_down_vol_up = (not price_up) and (vol_ratio_20d > 1.0)
    price_down_vol_down = (not price_up) and (vol_ratio_20d <= 1.0)
    
    features = {
        'vol_5d_avg': vol_5d_avg,
        'vol_20d_avg': vol_20d_avg,
        'vol_window_avg': vol_window_avg,
        'vol_ratio_20d': vol_ratio_20d,
        'is_volume_surge': is_volume_surge,
        'is_volume_shrink': is_volume_shrink,
        'price_up_vol_up': price_up_vol_up,
        'price_up_vol_down': price_up_vol_down,
        'price_down_vol_up': price_down_vol_up,
        'price_down_vol_down': price_down_vol_down
    }
    return features
