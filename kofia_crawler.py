import requests
from datetime import datetime, timedelta

def get_short_data(ticker):
    """네이버 금융에서 공매도 데이터 조회 - 세션 불필요"""
    try:
        url = f"https://api.finance.naver.com/service/itemSummary.nhn?itemcode={ticker}"
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.naver.com'}
        res = requests.get(url, headers=headers, timeout=10)
        print(f"[{ticker}] 상태: {res.status_code}")
        print(f"[{ticker}] 응답: {res.text[:300]}")
    except Exception as e:
        print(f"오류: {e}")

    # yfinance로 대체 데이터
    try:
        import yfinance as yf
        stock = yf.Ticker(f"{ticker}.KS")
        info = stock.info
        short_ratio = info.get('shortPercentOfFloat', 0) or 0
        print(f"[{ticker}] yfinance 공매도비율: {short_ratio}")
        return {
            'short_ratio': short_ratio * 100,
            'balance_change': 0,
            'short_balance': 0,
            'credit_ratio': 0
        }
    except Exception as e:
        print(f"yfinance 오류: {e}")

    return {'short_ratio': 0, 'balance_change': 0, 'short_balance': 0, 'credit_ratio': 0}

if __name__ == "__main__":
    print(get_short_data('005930'))
