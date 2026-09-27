import re
from typing import List, Dict

# スクリーナーでスキャン対象とする代表銘柄リスト（日本株＋米国株）
SAMPLE_SCREENER_TICKERS = [
    # 日本株 代表銘柄
    "3391.T", # ツルハHD
    "8306.T", # 三菱UFJ
    "8035.T", # 東京エレクトロン
    "6857.T", # アドバンテスト
    "7203.T", # トヨタ自動車
    "9984.T", # ソフトバンクグループ
    "6758.T", # ソニーグループ
    "7974.T", # 任天堂
    "8058.T", # 三菱商事
    "9104.T", # 商船三井
    "6501.T", # 日立製作所
    "4519.T", # 中外製薬
    
    # 米国株・ETF 代表銘柄
    "NVDA",   # NVIDIA
    "AAPL",   # Apple
    "MSFT",   # Microsoft
    "AMZN",   # Amazon
    "META",   # Meta
    "GOOGL",  # Alphabet (Google)
    "TSLA",   # Tesla
    "SPY",    # S&P 500 ETF
    "QQQ"     # NASDAQ 100 ETF
]

def format_ticker(symbol: str) -> str:
    """
    ユーザー入力のティッカーシンボルを正規化する。
    """
    symbol = symbol.strip().upper()
    if not symbol:
        return ""
    
    # ドットを含む場合はそのまま（例: 3391.T, BRK.B）
    if "." in symbol:
        return symbol
    
    # 数字4桁（日本株コード）
    if re.match(r"^\d{4}$", symbol):
        return f"{symbol}.T"
    
    # 新しい日本株コードフォーマット (数字3桁 + 英数字1桁)
    if re.match(r"^\d{3}[A-Z0-9]$", symbol):
        return f"{symbol}.T"
        
    return symbol
