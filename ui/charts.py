import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def calc_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """
    株価データフレームに 5MA, 25MA, 75MA を追加する。
    """
    df = df.copy()
    df['5MA'] = df['Close'].rolling(window=5).mean()
    df['25MA'] = df['Close'].rolling(window=25).mean()
    df['75MA'] = df['Close'].rolling(window=75).mean()
    return df

def create_candlestick_chart(df: pd.DataFrame, window_days: int = 40, title: str = "") -> go.Figure:
    """
    ローソク足 + 移動平均線 (5MA, 25MA, 75MA) + 出来高 の Plotly チャートを作成する。
    """
    # MA計算
    df_ma = calc_moving_averages(df)
    
    # 指定営業日分を切り出し
    chart_df = df_ma.tail(window_days).copy()
    
    # 日付フォーマット（表示用文字列）
    date_str = chart_df.index.strftime('%Y-%m-%d')
    
    # サブプロットの作成 (上段: 株価・MA, 下段: 出来高)
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(title or f"株価チャート (直近 {window_days} 営業日)", "出来高"),
        row_heights=[0.75, 0.25]
    )
    
    # 1. ローソク足
    fig.add_trace(
        go.Candlestick(
            x=date_str,
            open=chart_df['Open'],
            high=chart_df['High'],
            low=chart_df['Low'],
            close=chart_df['Close'],
            name="ローソク足",
            increasing_line_color='#EF5350',  # 陽線: 赤
            decreasing_line_color='#26A69A'   # 陰線: 緑/青
        ),
        row=1, col=1
    )
    
    # 2. 5日移動平均線
    fig.add_trace(
        go.Scatter(
            x=date_str,
            y=chart_df['5MA'],
            mode='lines',
            name='5MA',
            line=dict(color='#FF9800', width=1.5)  # オレンジ
        ),
        row=1, col=1
    )
    
    # 3. 25日移動平均線
    fig.add_trace(
        go.Scatter(
            x=date_str,
            y=chart_df['25MA'],
            mode='lines',
            name='25MA',
            line=dict(color='#2196F3', width=1.8)  # 青
        ),
        row=1, col=1
    )
    
    # 4. 75日移動平均線
    fig.add_trace(
        go.Scatter(
            x=date_str,
            y=chart_df['75MA'],
            mode='lines',
            name='75MA',
            line=dict(color='#9C27B0', width=1.8)  # 紫
        ),
        row=1, col=1
    )
    
    # 5. 出来高 (前日比で色分け)
    colors = []
    for i in range(len(chart_df)):
        if i == 0 or chart_df['Close'].iloc[i] >= chart_df['Close'].iloc[i-1]:
            colors.append('rgba(239, 83, 80, 0.7)')   # 陽線色
        else:
            colors.append('rgba(38, 166, 154, 0.7)')   # 陰線色

    fig.add_trace(
        go.Bar(
            x=date_str,
            y=chart_df['Volume'],
            name='出来高',
            marker_color=colors
        ),
        row=2, col=1
    )
    
    # レイアウトのカスタマイズ
    fig.update_layout(
        xaxis_rangeslider_visible=False,  # 下部のレンジスライダーはオフ（出来高が見やすいため）
        height=600,
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode='x unified',
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # X軸の土日空きスキップ（カテゴリ型として設定）
    fig.update_xaxes(type='category', row=1, col=1)
    fig.update_xaxes(type='category', row=2, col=1)
    
    return fig
