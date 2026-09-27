import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Any, List

def display_similarity_results_table(analyzed_cases: List[Dict[str, Any]]):
    """
    類似ケースの検索結果上位20件をテーブルで一覧表示する。
    """
    table_data = []
    for c in analyzed_cases:
        r_5d = f"{c['ret_5d']:+.1f}%" if c['ret_5d'] is not None else "N/A"
        r_10d = f"{c['ret_10d']:+.1f}%" if c['ret_10d'] is not None else "N/A"
        r_20d = f"{c['ret_20d']:+.1f}%" if c['ret_20d'] is not None else "N/A"
        max_up = f"{c['max_up_20d']:+.1f}%" if c['max_up_20d'] is not None else "N/A"
        max_down = f"{c['max_down_20d']:+.1f}%" if c['max_down_20d'] is not None else "N/A"
        
        table_data.append({
            "順位": f"{c['rank']}位",
            "類似度": f"{c['similarity_score']:.1f}",
            "過去期間": f"{c['start_date']} ～ {c['end_date']}",
            "基準日終値": f"{c['base_close']:,.1f}",
            "5日後": r_5d,
            "10日後": r_10d,
            "20日後": r_20d,
            "20日内最大上昇": max_up,
            "20日内最大下落": max_down
        })
        
    df_table = pd.DataFrame(table_data)
    st.dataframe(df_table, use_container_width=True, hide_index=True)

def display_statistics_summary(stats_dict: Dict[str, Any]):
    """
    上位類似ケースの統計および変動件数をカード型UIで表示する。
    """
    if not stats_dict:
        return
        
    total = stats_dict.get('total_cases', 0)
    s20 = stats_dict.get('stats_20d', {})
    counts = stats_dict.get('counts', {})
    
    st.markdown(f"#### 📊 過去類似ケース ({total}件) の統計サマリー")
    
    # メトリクス行 1: 5/10/20日後平均
    s5 = stats_dict.get('stats_5d', {})
    s10 = stats_dict.get('stats_10d', {})
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("5日後平均リターン", f"{s5.get('mean', 0.0):+.2f}%", f"中央値: {s5.get('median', 0.0):+.2f}%")
    m2.metric("10日後平均リターン", f"{s10.get('mean', 0.0):+.2f}%", f"中央値: {s10.get('median', 0.0):+.2f}%")
    m3.metric("20日後平均リターン", f"{s20.get('mean', 0.0):+.2f}%", f"中央値: {s20.get('median', 0.0):+.2f}%")
    m4.metric("20日後標準偏差", f"±{s20.get('std', 0.0):.2f}%", f"最大: {s20.get('max', 0.0):+.1f}% / 最小: {s20.get('min', 0.0):+.1f}%")
    
    st.markdown("---")
    st.markdown("##### 📈 20日後の値動き分布（観測された事実）")
    
    c_up1, c_up2, c_up3, c_dn1, c_dn2, c_dn3 = st.columns(6)
    c_up1.metric("+3%以上", f"{counts.get('plus_3', 0)} 件", f"/ {total} 件中")
    c_up2.metric("+5%以上", f"{counts.get('plus_5', 0)} 件", f"/ {total} 件中")
    c_up3.metric("+10%以上", f"{counts.get('plus_10', 0)} 件", f"/ {total} 件中")
    
    c_dn1.metric("-3%以下", f"{counts.get('minus_3', 0)} 件", f"/ {total} 件中")
    c_dn2.metric("-5%以下", f"{counts.get('minus_5', 0)} 件", f"/ {total} 件中")
    c_dn3.metric("-10%以下", f"{counts.get('minus_10', 0)} 件", f"/ {total} 件中")

def create_comparison_chart(target_norm: pd.DataFrame, top_case: Dict[str, Any]) -> go.Figure:
    """
    現在の100基準チャートと、類似度第1位の過去チャート（およびその後の20営業日）を重ね合わせて表示する。
    """
    fig = go.Figure()
    
    # 1. 現在のチャート (開始=100)
    t_x = list(range(1, len(target_norm) + 1))
    fig.add_trace(go.Scatter(
        x=t_x,
        y=target_norm['Norm_Close'],
        mode='lines',
        name='現在のチャート (100基準)',
        line=dict(color='#2196F3', width=3)
    ))
    
    # 2. 過去類似チャート (100基準)
    past_norm = top_case['past_norm_df']
    p_x = list(range(1, len(past_norm) + 1))
    fig.add_trace(go.Scatter(
        x=p_x,
        y=past_norm['Norm_Close'],
        mode='lines',
        name=f"類似1位 ({top_case['start_date']} ～ {top_case['end_date']})",
        line=dict(color='#FF9800', width=2, dash='solid')
    ))
    
    # 3. 過去類似チャートのその後 20営業日
    future_sub = top_case.get('future_sub_df')
    if future_sub is not None and not future_sub.empty:
        base_close = top_case['base_close']
        future_norm_close = (future_sub['Close'] / base_close) * past_norm['Norm_Close'].iloc[-1]
        
        f_x = list(range(len(past_norm) + 1, len(past_norm) + 1 + len(future_sub)))
        fig.add_trace(go.Scatter(
            x=f_x,
            y=future_norm_close,
            mode='lines',
            name="類似1位のその後20営業日",
            line=dict(color='#4CAF50', width=2, dash='dot')
        ))
        
    fig.update_layout(
        title=f"🔬 現在のチャート vs 類似1位 ({top_case['start_date']}～) の形状比較・その後追跡",
        xaxis_title="営業日経過 (100基準化)",
        yaxis_title="正規化価格 (開始=100)",
        template='plotly_white',
        height=450,
        hovermode='x unified',
        legend=dict(orientation="h", y=1.1, x=0)
    )
    return fig
