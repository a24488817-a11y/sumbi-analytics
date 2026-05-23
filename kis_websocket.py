"""
한투 WebSocket 실시간 체결 모듈
실시간 체결가/거래량 수신 → 세력 발자국 점수 즉시 반영
"""
import websocket, json, os, threading, time
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()
APP_KEY = os.environ.get("KIS_APP_KEY")
APP_SECRET = os.environ.get("KIS_APP_SECRET")

# 실시간 데이터 저장소
realtime_data = {}

def get_ws_approval_key():
    """WebSocket 접속키 발급"""
    url = "https://openapi.koreainvestment.com:9443/oauth2/Approval"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "secretkey": APP_SECRET
    }
    res = requests.post(url, headers=headers, json=body)
    return res.json().get("approval_key", "")

def on_message(ws, message):
    """실시간 체결 데이터 수신"""
    try:
        if message[0] == '0' or message[0] == '1':
            parts = message.split('|')
            if len(parts) >= 4:
                data = parts[3].split('^')
                if len(data) > 12:
                    ticker = data[0]
                    price = int(data[2])
                    volume = int(data[9])
                    strength = float(data[12]) if data[12] else 0

                    realtime_data[ticker] = {
                        'price': price,
                        'volume': volume,
                        'strength': strength,  # 체결강도
                        'time': datetime.now().strftime('%H:%M:%S')
                    }
    except:
        pass

def on_error(ws, error):
    print(f"[WS ERROR] {error}")

def on_close(ws, *args):
    print("[WS] 연결 종료")

def on_open(ws, approval_key, tickers):
    """종목 구독 등록"""
    for ticker in tickers:
        msg = {
            "header": {
                "approval_key": approval_key,
                "custtype": "P",
                "tr_type": "1",
                "content-type": "utf-8"
            },
            "body": {
                "input": {
                    "tr_id": "H0STCNT0",
                    "tr_key": ticker
                }
            }
        }
        ws.send(json.dumps(msg))
        print(f"[WS] 구독: {ticker}")

def start_websocket(tickers):
    """WebSocket 시작"""
    approval_key = get_ws_approval_key()
    if not approval_key:
        print("[WS] 접속키 발급 실패")
        return

    ws = websocket.WebSocketApp(
        "ws://ops.koreainvestment.com:21000",
        on_open=lambda ws: on_open(ws, approval_key, tickers),
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    t = threading.Thread(target=ws.run_forever)
    t.daemon = True
    t.start()
    print(f"[WS] 실시간 연결 시작: {tickers}")

def get_realtime(ticker):
    """종목 실시간 데이터 조회"""
    return realtime_data.get(ticker, {})
