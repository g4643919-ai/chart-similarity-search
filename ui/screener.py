import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from data_source.ticker_utils import SAMPLE_SCREENER_TICKERS
from data_source.yahoo_finance import fetch_stock_data
from analysis.feature_builder import build_all_features
from analysis.scoring import calculate_shape_score

def run_stock_screener(market_filter: str, min_score: int,
                       require_hl: bool, require_ma25_up: bool,
                       require_vol_up: bool, require_downward_end: bool) -> List[Dict[str, Any]]:
    """
    複数銘柄をスキャンし、条件を満たす銘柄をスコア順にランキング抽出する。
    """
    results = []
    
    # 対象銘柄のフィルタリング
    tickers_to_scan = []
    for ticker in SAMPLE_SCREENER_TICKERS:
        is_japan = ticker.endswith('.T')
        if market_filter == "すべて":
            tickers_to_scan.append(ticker)
        elif market_filter == "日本株" and is_japan:
            tickers_to_scan.append(ticker)
        elif market_filter == "米国株" and not is_japan:
            tickers_to_scan.append(ticker)
            
    for ticker in tickers_to_scan:
        df, info, err = fetch_stock_data(ticker, period="2y")
        if err or df is None or len(df) < 40:
            continue
            
        norm_df, features = build_all_features(df, window=40)
        shape_score_dict = calculate_shape_score(features, top_similarity_score=80.0)
        score = shape_score_dict['total_score']
        
        # 条件フィルター判定
        if score < min_score:
            continue
        if require_hl and not features.get('is_higher_low', False):
            continue
        if require_ma25_up and features.get('slope_25ma', 0.0) <= 0:
            continue
        if require_vol_up and features.get('vol_ratio_20d', 1.0) < 1.0:
            continue
        if require_downward_end and features.get('return_window', 0.0) >= 0:
            continue
            
        short_name = info.get('shortName', ticker) if info else ticker
        latest_close = df['Close'].iloc[-1]
        currency = info.get('currency', 'JPY') if info else 'JPY'
        curr_symbol = "円" if currency == "JPY" else "$"
        
        results.append({
            'ticker': ticker,
            'name': short_name,
            'score': score,
            'close': f"{latest_close:,.2f} {curr_symbol}",
            'return_40d': f"{features['return_window']:+.2f}%",
            'return_5d': f"{features['return_5d']:+.2f}%",
            'vol_ratio': f"{features['vol_ratio_20d']:.2f}倍",
            'trend': features['trend_structure'],
            'summary': features['chart_state_summary']
        })
        
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

def render_screener_ui():
    """
    チャート形状スクリーナー画面を描画する。
    """
    st.title("🔎 チャート形状スクリーナー")
    st.caption("現在、底練り・上昇転換などの特定のチャート形状になっている銘柄をスキャン検索します。")
    
    with st.sidebar:
        st.header("⚙️ スクリーナー条件設定")
        market_choice = st.radio("市場", ["すべて", "日本株", "米国株"], index=0)
        min_score = st.slider("最低形状適合スコア", 0, 100, 40, step=5)
        
        st.subheader("適用フィルター条件")
        req_hl = st.checkbox("安値切り上げ (HL)", value=True)
        req_ma25 = st.checkbox("25MA 上向き", value=False)
        req_vol = st.checkbox("出来高 20日平均以上", value=False)
        req_down_end = st.checkbox("下落後の底練り局面", value=False)
        
        scan_button = st.button("🔎 スクリーナー実行", use_container_width=True)
        
    st.info("左側のサイドバーで条件を設定し、「スクリーナー実行」を押してください。")
    
    if scan_button or st.session_state.get('auto_scan', True):
        st.session_state['auto_scan'] = False
        with st.spinner("対象銘柄のチャート特徴量をリアルタイムスキャン中..."):
            results = run_stock_screener(
                market_filter=market_choice,
                min_score=min_score,
                require_hl=req_hl,
                require_ma25_up=req_ma25,
                require_vol_up=req_vol,
                require_downward_end=req_down_end
            )
            
        if results:
            st.success(f"該当銘柄: {len(results)} 件検出")
            df_res = pd.DataFrame(results)
            df_res.columns = ["コード", "銘柄名", "形状スコア", "現在値", "40日騰落率", "5日騰落率", "出来高比率", "トレンド構造", "チャート状態概要"]
            st.dataframe(df_res, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("👉 検出銘柄の詳細分析")
            selected_ticker = st.selectbox("分析したい銘柄を選択", options=[r['ticker'] for r in results], format_func=lambda t: f"{t} - {next(r['name'] for r in results if r['ticker']==t)}")
            if st.button("この銘柄の分析ページを開く 📈"):
                st.session_state['selected_ticker_from_screener'] = selected_ticker
                st.session_state['nav_mode'] = "個別銘柄検索"
                st.rerun()
        else:
            st.warning("設定条件に一致する銘柄が見つかりませんでした。条件を緩めて再試行してください。")
