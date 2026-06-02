import yfinance as yf

tickers = {
    "미국채 10년물": "^TNX",
    "달러 인덱스": "DX-Y.NYB",
    "원/달러 환율": "KRW=X",
    "WTI 원유": "CL=F",
}

for name, symbol in tickers.items():
    try:
        data = yf.Ticker(symbol).history(period="2d")
        if not data.empty:
            last_price = data["Close"].iloc[-1]
            print(f"{name} ({symbol}): {last_price:.2f}")
        else:
            print(f"{name} ({symbol}): 데이터 없음")
    except Exception as e:
        print(f"{name} ({symbol}): 에러 - {e}")
