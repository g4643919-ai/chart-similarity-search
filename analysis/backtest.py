import pandas as pd
import numpy as np
from typing import Dict, Any, List
from analysis.similarity import search_similar_charts
from analysis.outcome_analysis import analyze_future_outcomes
from analysis.scoring import calculate_outcome_statistics

def run_walk_forward_backtest(df: pd.DataFrame, window_days: int = 40,
                               step_days: int = 60, max_evaluations: int = 15) -> Dict[str, Any]:
    """
    ウォークフォワード方式で過去の各時点（過去の「現在」）において
    類似形状検索を実行し、その後のパフォーマンスを集計検証する。
    """
    if len(df) < window_days * 3:
        return {'error': 'バックテストに必要なデータ期間が不足しています。'}
        
    evaluations = []
    
    # 過去の仮定基準日インデックスを生成（20営業日前のデータまで残す）
    # 最新の20営業日は未来追跡用
    end_limit = len(df) - 20 - 1
    start_limit = window_days * 2
    
    # スライド間隔 step_days ごとに過去基準日を取得
    eval_indices = list(range(start_limit, end_limit, step_days))
    if len(eval_indices) > max_evaluations:
        eval_indices = eval_indices[-max_evaluations:] # 直近 max_evaluations 回に絞る
        
    all_outcomes_20d = []
    all_outcomes_10d = []
    all_outcomes_5d = []
    
    for eval_idx in eval_indices:
        # その時点までのデータ（データリーク防止）
        df_until_eval = df.iloc[: eval_idx + 1].copy()
        eval_date = df_until_eval.index[-1].strftime('%Y-%m-%d')
        
        # 類似検索 (上位 5 件)
        similar_cases = search_similar_charts(df_until_eval, window_days=window_days, top_n=5)
        if not similar_cases:
            continue
            
        # 検索された各ケースの「未来20日」をその当時の基準日から追跡
        analyzed_cases = analyze_future_outcomes(df_until_eval, similar_cases)
        
        # 抽出された上位ケースのその後の平均値
        rets_20d = [c['ret_20d'] for c in analyzed_cases if c['ret_20d'] is not None]
        rets_10d = [c['ret_10d'] for c in analyzed_cases if c['ret_10d'] is not None]
        rets_5d = [c['ret_5d'] for c in analyzed_cases if c['ret_5d'] is not None]
        
        avg_20d = float(np.mean(rets_20d)) if rets_20d else 0.0
        avg_10d = float(np.mean(rets_10d)) if rets_10d else 0.0
        avg_5d = float(np.mean(rets_5d)) if rets_5d else 0.0
        
        # この仮定基準日からの実際の銘柄のその後の20日リターン
        future_real_sub = df.iloc[eval_idx + 1 : eval_idx + 1 + 20]
        real_ret_20d = None
        if len(future_real_sub) >= 20:
            real_ret_20d = ((future_real_sub['Close'].iloc[19] / df_until_eval['Close'].iloc[-1]) - 1) * 100
            
        all_outcomes_20d.extend(rets_20d)
        all_outcomes_10d.extend(rets_10d)
        all_outcomes_5d.extend(rets_5d)
        
        evaluations.append({
            'eval_date': eval_date,
            'top1_similarity': similar_cases[0]['similarity_score'],
            'predicted_avg_20d': avg_20d,
            'real_ret_20d': real_ret_20d
        })
        
    total_samples = len(all_outcomes_20d)
    if total_samples == 0:
        return {'error': 'バックテストのサンプル数が0件でした。'}
        
    arr_20d = np.array(all_outcomes_20d)
    arr_10d = np.array(all_outcomes_10d)
    arr_5d = np.array(all_outcomes_5d)
    
    summary = {
        'total_evaluations': len(evaluations),
        'total_samples': total_samples,
        'mean_5d': float(np.mean(arr_5d)),
        'mean_10d': float(np.mean(arr_10d)),
        'mean_20d': float(np.mean(arr_20d)),
        'median_20d': float(np.median(arr_20d)),
        'std_20d': float(np.std(arr_20d)),
        'max_20d': float(np.max(arr_20d)),
        'min_20d': float(np.min(arr_20d)),
        'plus_5_count': sum(1 for r in arr_20d if r >= 5.0),
        'minus_5_count': sum(1 for r in arr_20d if r <= -5.0),
        'evaluations_log': evaluations
    }
    return summary
