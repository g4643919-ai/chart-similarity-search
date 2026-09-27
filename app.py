import streamlit as st
import pandas as pd
from data_source.ticker_utils import format_ticker
from data_source.yahoo_finance import fetch_stock_data
from ui.charts import create_candlestick_chart
from analysis.feature_builder import build_all_features
from analysis.similarity import search_similar_charts
from analysis.outcome_analysis import analyze_future_outcomes
from analysis.scoring import calculate_outcome_statistics, calculate_shape_score
from analysis.backtest import run_walk_forward_backtest
from ui.tables import (
    display_similarity_results_table,
    display_statistics_summary,
    create_comparison_chart
)
from ui.screener import render_screener_ui

st.set_page_config(
    page_title="チャート形状検索エンジン",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# セッション状態の初期化
if 'nav_mode' not in st.session_state:
    st.session_state['nav_mode'] = "個別銘柄検索"
if 'search_input' not in st.session_state:
    st.session_state['search_input'] = "3391"

# スクリーナーからのジャンプ処理
if 'selected_ticker_from_screener' in st.session_state:
    st.session_state['search_input'] = st.session_state.pop('selected_ticker_from_screener')

# サイドバーによるモード切替
with st.sidebar:
    st.title("📈 チャート形状検索")
    st.caption("Ver 3.0 | 過去パターン検索エンジン")
    
    nav_mode = st.radio(
        "機能切り替え",
        ["個別銘柄検索", "チャート形状スクリーナー"],
        index=0 if st.session_state['nav_mode'] == "個別銘柄検索" else 1,
        key="sidebar_nav"
    )
    st.session_state['nav_mode'] = nav_mode
    st.markdown("---")

if st.session_state['nav_mode'] == "チャート形状スクリーナー":
    render_screener_ui()
else:
    # --- 個別銘柄検索・分析画面 ---
    st.title("📈 チャート形状検索エンジン")
    st.caption("株価予測AIではなく、過去10年の株式市場から類似のチャート形状を検索するパターン検索ツール")

    # クイック検索ボタン（スマホでもタップしやすい大きめのボタン）
    st.markdown("**🔍 クイック検索例**")
    q_col1, q_col2, q_col3, q_col4, q_col5 = st.columns(5)
    if q_col1.button("3391 ツルハHD", use_container_width=True):
        st.session_state['search_input'] = "3391"
    if q_col2.button("8306 三菱UFJ", use_container_width=True):
        st.session_state['search_input'] = "8306"
    if q_col3.button("8035 東エレク", use_container_width=True):
        st.session_state['search_input'] = "8035"
    if q_col4.button("NVDA エヌビディア", use_container_width=True):
        st.session_state['search_input'] = "NVDA"
    if q_col5.button("AAPL アップル", use_container_width=True):
        st.session_state['search_input'] = "AAPL"

    st.write("")
    
    # 検索フォーム
    col1, col2 = st.columns([3, 1])
    with col1:
        user_input = st.text_input(
            "銘柄コード・ティッカーを入力",
            value=st.session_state['search_input'],
            placeholder="例: 3391, 8306, 8035, NVDA, AAPL, SPY",
            key="ticker_text_field"
        )
    with col2:
        st.write("")
        st.write("")
        search_clicked = st.button("検索 🔍", use_container_width=True)

    formatted_symbol = format_ticker(user_input)

    if formatted_symbol:
        with st.spinner(f"yfinance から {formatted_symbol} の株価データを取得中..."):
            df, info, error_msg = fetch_stock_data(formatted_symbol, period="10y")
            
        if error_msg:
            st.error(error_msg)
        elif df is not None and not df.empty:
            short_name = info.get('shortName', formatted_symbol) if info else formatted_symbol
            latest_date = df.index[-1].strftime('%Y-%m-%d')
            latest_close = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[-2] if len(df) >= 2 else latest_close
            change = latest_close - prev_close
            change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
            currency = info.get('currency', 'JPY') if info else 'JPY'
            currency_symbol = "円" if currency == "JPY" else "$"
            
            # ① 銘柄情報 Header & ② 現在価格
            st.header(f"{short_name} ({formatted_symbol})")
            
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("現在値 (終値)", f"{latest_close:,.2f} {currency_symbol}", f"{change:+.2f} ({change_pct:+.2f}%)")
            m_col2.metric("最新データ日付", latest_date)
            
            if info and info.get('fiftyTwoWeekHigh'):
                m_col3.metric("52週高値", f"{info['fiftyTwoWeekHigh']:,.2f} {currency_symbol}")
            else:
                m_col3.metric("過去最高値", f"{df['High'].max():,.2f} {currency_symbol}")
                
            if info and info.get('fiftyTwoWeekLow'):
                m_col4.metric("52週安値", f"{info['fiftyTwoWeekLow']:,.2f} {currency_symbol}")
            else:
                m_col4.metric("過去最安値", f"{df['Low'].min():,.2f} {currency_symbol}")
                
            st.markdown("---")
            
            # ③ 現在のチャート & 分析期間設定
            c_title_col, c_opt_col = st.columns([2, 1])
            with c_title_col:
                st.subheader("📈 ③ 現在のチャート (ローソク足 + 5/25/75MA + 出来高)")
            with c_opt_col:
                window_days = st.radio(
                    "分析対象期間",
                    options=[20, 40, 60, 120],
                    index=1,  # デフォルト 40営業日
                    format_func=lambda x: f"{x}営業日",
                    horizontal=True
                )
                
            norm_df, features = build_all_features(df, window=window_days)
            fig_current = create_candlestick_chart(df, window_days=window_days, title=f"{short_name} (直近 {window_days} 営業日)")
            st.plotly_chart(fig_current, use_container_width=True)
            
            # 過去類似検索
            with st.spinner("過去チャートの形状マッチング・類似度計算を実行中..."):
                similar_cases = search_similar_charts(df, window_days=window_days, top_n=20)
                analyzed_cases = analyze_future_outcomes(df, similar_cases)
                stats_dict = calculate_outcome_statistics(analyzed_cases)
                top_score = similar_cases[0]['similarity_score'] if similar_cases else 0.0
                
            # ④ チャート状態 & ⑤ チャート形状スコア
            st.subheader("🔍 ④ チャート状態 & ⑤ チャート形状スコア")
            shape_score_dict = calculate_shape_score(features, top_similarity_score=top_score)
            
            score_col1, score_col2 = st.columns([1, 2])
            with score_col1:
                st.metric("チャート形状スコア", f"{shape_score_dict['total_score']} / {shape_score_dict['max_possible']}")
                st.caption("※上昇確率ではなく、パターン特徴条件への適合度を表します。")
            with score_col2:
                st.info(f"**チャート状態分類:** `{features['chart_state_summary']}`")
                
            with st.expander("🔬 チャート形状スコア内訳・抽出特徴量詳細を見る"):
                sb = shape_score_dict['breakdown']
                s_c1, s_c2, s_c3, s_c4, s_c5 = st.columns(5)
                s_c1.metric("下落終了 (10)", f"{sb['downward_end']:.1f}")
                s_c2.metric("安値圏 (10)", f"{sb['near_low']:.1f}")
                s_c3.metric("安値切り上げ (15)", f"{sb['higher_low']:.1f}")
                s_c4.metric("出来高 (15)", f"{sb['volume']:.1f}")
                s_c5.metric("25MA (10)", f"{sb['ma25']:.1f}")
                
                st.markdown("---")
                f_col1, f_col2, f_col3, f_col4 = st.columns(4)
                with f_col1:
                    st.markdown("**【価格・騰落率】**")
                    st.write(f"- 直近{window_days}日騰落率: **{features['return_window']:+.2f}%**")
                    st.write(f"- 5日騰落率: **{features['return_5d']:+.2f}%**")
                    st.write(f"- 20日騰落率: **{features['return_20d']:+.2f}%**")
                    st.write(f"- 高値からの下落率: **{features['drawdown_from_high']:.2f}%**")
                    st.write(f"- レンジ相対位置: **{features['range_position']*100:.1f}%**")
                with f_col2:
                    st.markdown("**【移動平均・トレンド】**")
                    st.write(f"- 25MA乖離率: **{features['dev_25ma']:+.2f}%**")
                    st.write(f"- 75MA乖離率: **{features['dev_75ma']:+.2f}%**")
                    st.write(f"- 25MA傾き(5日): **{features['slope_25ma']:+.2f}%**")
                    st.write(f"- トレンド構造: **{features['trend_structure']}**")
                with f_col3:
                    st.markdown("**【ローソク足・出来高】**")
                    st.write(f"- 直近ローソク足: **{features['candle_type']}**")
                    st.write(f"- 出来高/20日平均: **{features['vol_ratio_20d']:.2f}倍**")
                    st.write(f"- 出来高急増: **{'検知' if features['is_volume_surge'] else 'なし'}**")
                with f_col4:
                    st.markdown("**【100基準スケーリング】**")
                    st.write(f"- 開始価格: **100.00**")
                    st.write(f"- 最新正規化終値: **{norm_df['Norm_Close'].iloc[-1]:.2f}**")
                    
            st.markdown("---")
            
            # ⑥ 過去の類似チャート検索 & ⑦ その後の値動き
            st.subheader("🔎 ⑥ 過去の類似チャート検索 & ⑦ その後の値動き分析")
            if analyzed_cases:
                display_similarity_results_table(analyzed_cases)
                
                st.markdown("---")
                # ⑧ 統計
                st.subheader("📊 ⑧ 過去類似ケースのその後の統計")
                display_statistics_summary(stats_dict)
                
                st.markdown("---")
                # ⑨ 類似ケース比較チャート & ⑩ 類似度の内訳
                st.subheader("🔬 ⑨ 類似チャート比較 & 類似度内訳")
                top_1 = analyzed_cases[0]
                fig_comp = create_comparison_chart(norm_df, top_1)
                st.plotly_chart(fig_comp, use_container_width=True)
                
                with st.expander(f"📌 類似度第1位 ({top_1['start_date']}～) の類似度スコア内訳"):
                    b = top_1['breakdown']
                    bd_col1, bd_col2, bd_col3, bd_col4 = st.columns(4)
                    bd_col1.metric("総合類似度スコア", f"{top_1['similarity_score']:.1f} / 100")
                    bd_col2.metric("価格形状 (30%)", f"{b['price_shape']:.1f}")
                    bd_col3.metric("高値安値構造 (15%)", f"{b['trend_structure']:.1f}")
                    bd_col4.metric("価格変化率 (15%)", f"{b['return_rate']:.1f}")
                    
                    bd_col5, bd_col6, bd_col7, bd_col8 = st.columns(4)
                    bd_col5.metric("出来高構造 (15%)", f"{b['volume']:.1f}")
                    bd_col6.metric("移動平均関係 (10%)", f"{b['ma_relation']:.1f}")
                    bd_col7.metric("レンジ構造 (10%)", f"{b['range']:.1f}")
                    bd_col8.metric("ローソク足 (5%)", f"{b['candlestick']:.1f}")
                    
                st.markdown("---")
                # ⑩ バックテスト検証
                st.subheader("🧪 ⑩ バックテスト検証 (ウォークフォワード方式)")
                st.caption("過去の各時点を「当時の現在」と仮定し、類似形状検索の過去パフォーマンスを検証します。")
                
                if st.button("バックテストを実行する 🚀"):
                    with st.spinner("過去の各時点でのウォークフォワードバックテストを実行中..."):
                        bt_res = run_walk_forward_backtest(df, window_days=window_days, step_days=60, max_evaluations=15)
                        
                    if 'error' in bt_res:
                        st.warning(bt_res['error'])
                    else:
                        st.success(f"バックテスト完了: 検証過去時点 {bt_res['total_evaluations']} 回 / 全 {bt_res['total_samples']} サンプル")
                        
                        bt_m1, bt_m2, bt_m3, bt_m4 = st.columns(4)
                        bt_m1.metric("5日後平均リターン", f"{bt_res['mean_5d']:+.2f}%")
                        bt_m2.metric("10日後平均リターン", f"{bt_res['mean_10d']:+.2f}%")
                        bt_m3.metric("20日後平均リターン", f"{bt_res['mean_20d']:+.2f}%", f"中央値: {bt_res['median_20d']:+.2f}%")
                        bt_m4.metric("20日後 +5%以上件数", f"{bt_res['plus_5_count']} 件", f"/ -5%以下: {bt_res['minus_5_count']} 件")
                        
                        with st.expander("📋 バックテスト検証ログ詳細"):
                            df_bt_log = pd.DataFrame(bt_res['evaluations_log'])
                            df_bt_log.columns = ["過去仮定基準日", "類似1位スコア", "類似上位予測20日後平均%", "実際のその後の20日後%"]
                            st.dataframe(df_bt_log, use_container_width=True)
                            
            else:
                st.warning("過去類似ケースの抽出データが不十分でした。")

# フッター免責事項
st.divider()
st.caption("""
**⚠️ 投資に関する注意・利用規約**  
本サイトで提供する情報は、過去の株価・チャートデータをもとにした統計的・分析的な情報を提供することを目的としたものであり、特定の金融商品についての投資助言、売買推奨、投資勧誘を目的とするものではありません。
過去のチャート形状や過去の類似ケースにおける値動きは、将来の株価の動きを保証するものではありません。
類似度スコア、チャート形状スコア、過去の騰落率、統計情報等は、将来の利益や損失を予測・保証するものではありません。
本サイトの情報を利用した投資判断およびその結果については、利用者自身の責任において行うものとします。投資には元本割れ等のリスクがあります。
""")
