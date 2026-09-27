import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from analysis.feature_builder import build_all_features
from analysis.price_features import normalize_prices

def calculate_similarity_breakdown(target_norm: pd.DataFrame, target_feat: Dict[str, Any],
                                   past_norm: pd.DataFrame, past_feat: Dict[str, Any]) -> Dict[str, float]:
    """
    現在の40営業日チャートと過去の40営業日チャートの類似度内訳（0～100）を計算する。
    """
    # 1. 価格形状 (Normalized Close の Pearson相関およびRMSE)
    t_close = target_norm['Norm_Close'].values
    p_close = past_norm['Norm_Close'].values
    
    if len(t_close) == len(p_close) and len(t_close) > 1:
        # 相関係数 (-1 ~ 1 -> 0 ~ 100)
        corr = np.corrcoef(t_close, p_close)[0, 1]
        corr_score = max(0.0, float(corr) * 100) if not np.isnan(corr) else 50.0
        
        # 平均絶対誤差 (MAE) スコア
        mae = np.mean(np.abs(t_close - p_close))
        mae_score = max(0.0, 100.0 - (mae * 3.0)) # MAEが小さいほど高得点
        
        price_shape_score = (corr_score * 0.7) + (mae_score * 0.3)
    else:
        price_shape_score = 50.0
        
    # 2. 高値・安値構造 (HH, HL, LH, LL および レンジ相対位置の一致度)
    hl_match = 100.0 if target_feat.get('is_higher_low') == past_feat.get('is_higher_low') else 40.0
    hh_match = 100.0 if target_feat.get('is_higher_high') == past_feat.get('is_higher_high') else 40.0
    trend_match = 100.0 if target_feat.get('trend_structure') == past_feat.get('trend_structure') else 50.0
    trend_structure_score = (hl_match * 0.4) + (hh_match * 0.3) + (trend_match * 0.3)
    
    # 3. 価格変化率 (1/5/20/window日騰落率の近さ)
    diff_ret_w = abs(target_feat.get('return_window', 0) - past_feat.get('return_window', 0))
    diff_ret_5d = abs(target_feat.get('return_5d', 0) - past_feat.get('return_5d', 0))
    diff_ret_20d = abs(target_feat.get('return_20d', 0) - past_feat.get('return_20d', 0))
    ret_diff_avg = (diff_ret_w + diff_ret_5d + diff_ret_20d) / 3.0
    return_rate_score = max(0.0, 100.0 - (ret_diff_avg * 3.0))
    
    # 4. 出来高構造 (20日比率・変化率の近さ)
    diff_vol_ratio = abs(target_feat.get('vol_ratio_20d', 1.0) - past_feat.get('vol_ratio_20d', 1.0))
    surge_match = 100.0 if target_feat.get('is_volume_surge') == past_feat.get('is_volume_surge') else 50.0
    volume_score = (max(0.0, 100.0 - (diff_vol_ratio * 30.0)) * 0.6) + (surge_match * 0.4)
    
    # 5. 移動平均関係 (25MA/75MA 乖離率・傾きの一致度)
    diff_dev25 = abs(target_feat.get('dev_25ma', 0) - past_feat.get('dev_25ma', 0))
    diff_slope25 = abs(target_feat.get('slope_25ma', 0) - past_feat.get('slope_25ma', 0))
    ma_above_match = 100.0 if target_feat.get('is_above_25ma') == past_feat.get('is_above_25ma') else 40.0
    ma_score = (max(0.0, 100.0 - (diff_dev25 * 4.0)) * 0.4) + (max(0.0, 100.0 - (diff_slope25 * 5.0)) * 0.3) + (ma_above_match * 0.3)
    
    # 6. レンジ (レンジ位置・レンジ幅比率)
    diff_range_pos = abs(target_feat.get('range_position', 0.5) - past_feat.get('range_position', 0.5))
    diff_range_ratio = abs(target_feat.get('range_ratio', 0) - past_feat.get('range_ratio', 0))
    range_score = (max(0.0, 100.0 - (diff_range_pos * 100.0)) * 0.6) + (max(0.0, 100.0 - (diff_range_ratio * 3.0)) * 0.4)
    
    # 7. ローソク足構造 (下ヒゲ・実体比率)
    diff_body = abs(target_feat.get('latest_body_ratio', 0) - past_feat.get('latest_body_ratio', 0))
    diff_lower = abs(target_feat.get('latest_lower_ratio', 0) - past_feat.get('latest_lower_ratio', 0))
    type_match = 100.0 if target_feat.get('candle_type') == past_feat.get('candle_type') else 60.0
    candle_score = (max(0.0, 100.0 - (diff_body * 80.0)) * 0.3) + (max(0.0, 100.0 - (diff_lower * 80.0)) * 0.3) + (type_match * 0.4)
    
    return {
        'price_shape': min(100.0, max(0.0, price_shape_score)),
        'trend_structure': min(100.0, max(0.0, trend_structure_score)),
        'return_rate': min(100.0, max(0.0, return_rate_score)),
        'volume': min(100.0, max(0.0, volume_score)),
        'ma_relation': min(100.0, max(0.0, ma_score)),
        'range': min(100.0, max(0.0, range_score)),
        'candlestick': min(100.0, max(0.0, candle_score))
    }

def calculate_total_similarity(breakdown: Dict[str, float]) -> float:
    """
    設定ウェイトに基づいて総合類似度スコア (0～100) を計算する。
    ウェイト:
      価格形状 30% / 高値安値 15% / 価格変化率 15% / 出来高 15% / MA関係 10% / レンジ 10% / ローソク足 5%
    """
    total = (
        breakdown['price_shape'] * 0.30 +
        breakdown['trend_structure'] * 0.15 +
        breakdown['return_rate'] * 0.15 +
        breakdown['volume'] * 0.15 +
        breakdown['ma_relation'] * 0.10 +
        breakdown['range'] * 0.10 +
        breakdown['candlestick'] * 0.05
    )
    return float(np.round(total, 1))

def search_similar_charts(df: pd.DataFrame, window_days: int = 40, top_n: int = 20) -> List[Dict[str, Any]]:
    """
    全データフレームから過去のローリングウィンドウ（データリーク防止）を検索し、
    現在のチャート形状と最も類似した上位 top_n 件のケースを抽出する。
    """
    if len(df) < window_days * 2:
        return []
        
    # 現在のターゲット（最新 window_days 営業日）
    target_df = df.tail(window_days).copy()
    target_norm, target_feat = build_all_features(target_df, window=window_days)
    target_end_date = target_df.index[-1]
    
    results = []
    
    # 過去データのローリング検索（最新の直近ウィンドウを除外するため、1営業日以上前を検索対象とする）
    # 検索範囲: 0 ～ (len(df) - window_days - 1)
    max_idx = len(df) - window_days - 1
    
    # 処理の高速化のため、ステップ数 1営業日ずつスライド
    for i in range(0, max_idx + 1):
        past_sub = df.iloc[i : i + window_days].copy()
        past_end_date = past_sub.index[-1]
        
        # 重複/近接防止: 直近30営業日以内の過去期間は同一局面とみなしてスキップ（最新ターゲットとの直接重なり防止）
        if (target_end_date - past_end_date).days < 30:
            continue
            
        past_norm, past_feat = build_all_features(past_sub, window=window_days)
        
        breakdown = calculate_similarity_breakdown(target_norm, target_feat, past_norm, past_feat)
        total_score = calculate_total_similarity(breakdown)
        
        results.append({
            'start_idx': i,
            'end_idx': i + window_days - 1,
            'start_date': past_sub.index[0].strftime('%Y-%m-%d'),
            'end_date': past_end_date.strftime('%Y-%m-%d'),
            'base_date': past_end_date, # 未来結果計算の基準日
            'base_close': past_sub['Close'].iloc[-1],
            'similarity_score': total_score,
            'breakdown': breakdown,
            'past_sub_df': past_sub,
            'past_norm_df': past_norm
        })
        
    # スコアで降順ソート
    results.sort(key=lambda x: x['similarity_score'], reverse=True)
    
    # 近接する過去期間（15営業日以内の重複ウィンドウ）の重複排除フィルタ
    filtered_results = []
    used_dates = []
    
    for item in results:
        b_date = item['base_date']
        is_too_close = False
        for u_date in used_dates:
            if abs((b_date - u_date).days) < 20: # 20日以内の重複は除外
                is_too_close = True
                break
        if not is_too_close:
            filtered_results.append(item)
            used_dates.append(b_date)
            if len(filtered_results) >= top_n:
                break
                
    # 1位, 2位... と順位を付与
    for rank, item in enumerate(filtered_results, start=1):
        item['rank'] = rank
        
    return filtered_results
