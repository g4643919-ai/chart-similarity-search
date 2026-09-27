import pandas as pd
import numpy as np
from typing import Dict, Any, List

# デフォルトの形状スコア重み（config.py からもカスタマイズ可能）
DEFAULT_SCORE_WEIGHTS = {
    'downward_end': 10,       # 下落終了状態
    'near_low': 10,           # 安値圏への近さ
    'higher_low': 15,         # 安値切り上げ
    'candlestick': 10,        # ローソク足
    'volume': 15,             # 出来高
    'ma25': 10,               # 25MA
    'ma75': 5,                # 75MA
    'range_formation': 10,    # レンジ形成
    'range_breakout': 5,      # レンジブレイク
    'past_similarity': 10     # 過去類似形状
}

def calculate_shape_score(features: Dict[str, Any], top_similarity_score: float = 0.0,
                          weights: Dict[str, int] = None) -> Dict[str, Any]:
    """
    現在のチャートが各種テクニカルパターン条件（底練り・上昇転換など）に
    どの程度当てはまっているかを 0～100 でスコア化する。
    ※上昇確率の予測ではなく、条件適合度を表す。
    """
    if weights is None:
        weights = DEFAULT_SCORE_WEIGHTS
        
    scores = {}
    
    # 1. 下落終了状態 (10点): 騰落率はマイナスだが下落速度が鈍化、または直近反発
    ret_w = features.get('return_window', 0.0)
    ret_5d = features.get('return_5d', 0.0)
    if ret_w < -5.0 and ret_5d >= -1.0:
        scores['downward_end'] = weights['downward_end'] * 1.0
    elif ret_w < 0 and ret_5d > 0:
        scores['downward_end'] = weights['downward_end'] * 0.7
    else:
        scores['downward_end'] = weights['downward_end'] * 0.3
        
    # 2. 安値圏への近さ (10点): レンジ位置が 0.0 ～ 0.4 付近
    r_pos = features.get('range_position', 0.5)
    if r_pos <= 0.3:
        scores['near_low'] = weights['near_low'] * 1.0
    elif r_pos <= 0.5:
        scores['near_low'] = weights['near_low'] * 0.6
    else:
        scores['near_low'] = weights['near_low'] * 0.2
        
    # 3. 安値切り上げ (15点): Higher Low (HL)
    if features.get('is_higher_low', False):
        scores['higher_low'] = weights['higher_low'] * 1.0
    else:
        scores['higher_low'] = 0.0
        
    # 4. ローソク足 (10点): 下ヒゲまたは陽線
    lower_r = features.get('latest_lower_ratio', 0.0)
    is_bull = features.get('is_bullish', False)
    if lower_r > 0.4 and is_bull:
        scores['candlestick'] = weights['candlestick'] * 1.0
    elif lower_r > 0.3 or is_bull:
        scores['candlestick'] = weights['candlestick'] * 0.6
    else:
        scores['candlestick'] = weights['candlestick'] * 0.2
        
    # 5. 出来高 (15点): 20日平均以上または増加
    vol_r = features.get('vol_ratio_20d', 1.0)
    if vol_r >= 1.3:
        scores['volume'] = weights['volume'] * 1.0
    elif vol_r >= 1.0:
        scores['volume'] = weights['volume'] * 0.7
    else:
        scores['volume'] = weights['volume'] * 0.3
        
    # 6. 25MA (10点): 株価が25MAより上、または25MAが上向き
    slope25 = features.get('slope_25ma', 0.0)
    is_above25 = features.get('is_above_25ma', False)
    if is_above25 and slope25 > 0:
        scores['ma25'] = weights['ma25'] * 1.0
    elif is_above25 or slope25 > 0:
        scores['ma25'] = weights['ma25'] * 0.6
    else:
        scores['ma25'] = weights['ma25'] * 0.2
        
    # 7. 75MA (5点): 75MAより上
    if features.get('is_above_75ma', False):
        scores['ma75'] = weights['ma75'] * 1.0
    else:
        scores['ma75'] = weights['ma75'] * 0.3
        
    # 8. レンジ形成 (10点): ボラティリティ縮小
    if features.get('volatility_contracting', False):
        scores['range_formation'] = weights['range_formation'] * 1.0
    else:
        scores['range_formation'] = weights['range_formation'] * 0.5
        
    # 9. レンジブレイク (5点): レンジ上限 (range_position > 0.7) 付近
    if r_pos >= 0.7:
        scores['range_breakout'] = weights['range_breakout'] * 1.0
    else:
        scores['range_breakout'] = weights['range_breakout'] * 0.3
        
    # 10. 過去類似形状 (10点): 上位類似度スコア
    scores['past_similarity'] = weights['past_similarity'] * (min(100.0, top_similarity_score) / 100.0)
    
    total_score = float(np.round(sum(scores.values()), 1))
    
    return {
        'total_score': total_score,
        'max_possible': sum(weights.values()),
        'breakdown': scores
    }

def calculate_outcome_statistics(analyzed_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    類似ケース群について、5日・10日・20日後の騰落統計および閾値別件数を集計する。
    """
    if not analyzed_cases:
        return {}
        
    ret_5d_list = [c['ret_5d'] for c in analyzed_cases if c['ret_5d'] is not None]
    ret_10d_list = [c['ret_10d'] for c in analyzed_cases if c['ret_10d'] is not None]
    ret_20d_list = [c['ret_20d'] for c in analyzed_cases if c['ret_20d'] is not None]
    
    total_valid = len(ret_20d_list)
    
    def calc_stats(series_list):
        if not series_list:
            return {'mean': 0.0, 'median': 0.0, 'std': 0.0, 'max': 0.0, 'min': 0.0}
        arr = np.array(series_list)
        return {
            'mean': float(np.mean(arr)),
            'median': float(np.median(arr)),
            'std': float(np.std(arr)),
            'max': float(np.max(arr)),
            'min': float(np.min(arr))
        }
        
    stats_5d = calc_stats(ret_5d_list)
    stats_10d = calc_stats(ret_10d_list)
    stats_20d = calc_stats(ret_20d_list)
    
    count_plus_3 = sum(1 for r in ret_20d_list if r >= 3.0)
    count_plus_5 = sum(1 for r in ret_20d_list if r >= 5.0)
    count_plus_10 = sum(1 for r in ret_20d_list if r >= 10.0)
    
    count_minus_3 = sum(1 for r in ret_20d_list if r <= -3.0)
    count_minus_5 = sum(1 for r in ret_20d_list if r <= -5.0)
    count_minus_10 = sum(1 for r in ret_20d_list if r <= -10.0)
    
    return {
        'total_cases': len(analyzed_cases),
        'valid_cases': total_valid,
        'stats_5d': stats_5d,
        'stats_10d': stats_10d,
        'stats_20d': stats_20d,
        'counts': {
            'plus_3': count_plus_3,
            'plus_5': count_plus_5,
            'plus_10': count_plus_10,
            'minus_3': count_minus_3,
            'minus_5': count_minus_5,
            'minus_10': count_minus_10
        }
    }
