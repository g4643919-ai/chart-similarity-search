import pandas as pd
from typing import Dict, Any, Tuple
from analysis.price_features import normalize_prices, extract_price_features
from analysis.candle_features import extract_candle_features
from analysis.volume_features import extract_volume_features
from analysis.trend_features import extract_trend_features
from analysis.range_features import extract_range_features

def classify_chart_state(features: Dict[str, Any]) -> str:
    """
    特徴量に基づいて現在のチャート状態（定性分類）を説明する。
    ※ 投資推奨ではなく事実としての構造説明。
    """
    ret_w = features.get('return_window', 0.0)
    trend_str = features.get('trend_structure', '')
    is_hl = features.get('is_higher_low', False)
    dev_25 = features.get('dev_25ma', 0.0)
    vol_shrink = features.get('volatility_contracting', False)
    vol_expand = features.get('volatility_expanding', False)
    range_pos = features.get('range_position', 0.5)
    
    states = []
    
    # 1. 大まかな価格方向
    if ret_w < -10.0:
        states.append("下落傾向")
    elif ret_w > 10.0:
        states.append("上昇傾向")
    else:
        states.append("レンジ・保ち合い")
        
    # 2. ボラティリティ状態
    if vol_shrink:
        states.append("ボラティリティ縮小 (保ち合い)")
    elif vol_expand:
        states.append("ボラティリティ拡大")
        
    # 3. 安値切り上げやトレンド転換の兆候
    if is_hl and ret_w < 0:
        states.append("底値圏での安値切り上げ")
    elif is_hl and ret_w >= 0:
        states.append("上昇展開（安値切り上げ）")
        
    # 4. 移動平均線位置
    if dev_25 < -5.0:
        states.append("25MA下方乖離 (売られすぎ水準)")
    elif dev_25 > 5.0:
        states.append("25MA上方乖離")
        
    # 5. レンジ内の位置
    if range_pos <= 0.2:
        states.append("直近レンジ下限付近")
    elif range_pos >= 0.8:
        states.append("直近レンジ上限付近")
        
    return " → ".join(states)

def build_all_features(df: pd.DataFrame, window: int = 40) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    指定された window (デフォルト40営業日) の株価データから:
    1. 100基準に正規化したデータフレーム
    2. 全特徴量の統合辞書
    を生成して返す。
    """
    sub_df = df.tail(window).copy()
    norm_df = normalize_prices(sub_df)
    
    # 各領域の特徴量を抽出
    p_feat = extract_price_features(df, window=window)
    c_feat = extract_candle_features(df, window=window)
    v_feat = extract_volume_features(df, window=window)
    t_feat = extract_trend_features(df, window=window)
    r_feat = extract_range_features(df, window=window)
    
    # 辞書統合
    all_features = {}
    all_features.update(p_feat)
    all_features.update(c_feat)
    all_features.update(v_feat)
    all_features.update(t_feat)
    all_features.update(r_feat)
    
    # 現在のチャート状態の定性分類
    all_features['chart_state_summary'] = classify_chart_state(all_features)
    
    return norm_df, all_features
