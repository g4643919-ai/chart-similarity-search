import pandas as pd
import numpy as np
from typing import Dict, Any, List

def analyze_future_outcomes(full_df: pd.DataFrame, similar_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    抽出された過去類似ケースごとに、基準日より後の未来データ (5, 10, 20営業日後) の値動きを追跡・計算する。
    データリークを防止するため、類似度計算済みの類似ケース情報に事後的に追記する。
    """
    analyzed_cases = []
    
    for case in similar_cases:
        end_idx = case['end_idx']
        base_close = case['base_close']
        
        # 基準日以降のデータを取得 (最大20営業日分)
        future_sub = full_df.iloc[end_idx + 1 : end_idx + 1 + 20]
        
        ret_5d = None
        ret_10d = None
        ret_20d = None
        max_up_20d = None
        max_down_20d = None
        
        if len(future_sub) >= 1:
            # 5営業日後
            if len(future_sub) >= 5:
                c5 = future_sub['Close'].iloc[4]
                ret_5d = ((c5 / base_close) - 1) * 100
            elif len(future_sub) > 0:
                c5 = future_sub['Close'].iloc[-1]
                ret_5d = ((c5 / base_close) - 1) * 100
                
            # 10営業日後
            if len(future_sub) >= 10:
                c10 = future_sub['Close'].iloc[9]
                ret_10d = ((c10 / base_close) - 1) * 100
            elif len(future_sub) > 0:
                c10 = future_sub['Close'].iloc[-1]
                ret_10d = ((c10 / base_close) - 1) * 100
                
            # 20営業日後
            if len(future_sub) >= 20:
                c20 = future_sub['Close'].iloc[19]
                ret_20d = ((c20 / base_close) - 1) * 100
            elif len(future_sub) > 0:
                c20 = future_sub['Close'].iloc[-1]
                ret_20d = ((c20 / base_close) - 1) * 100
                
            # 未来20営業日以内の最大高値・最大安値
            max_high = future_sub['High'].max()
            min_low = future_sub['Low'].min()
            
            max_up_20d = ((max_high / base_close) - 1) * 100
            max_down_20d = ((min_low / base_close) - 1) * 100
            
        case_copy = dict(case)
        case_copy['ret_5d'] = ret_5d
        case_copy['ret_10d'] = ret_10d
        case_copy['ret_20d'] = ret_20d
        case_copy['max_up_20d'] = max_up_20d
        case_copy['max_down_20d'] = max_down_20d
        case_copy['future_sub_df'] = future_sub
        
        analyzed_cases.append(case_copy)
        
    return analyzed_cases
