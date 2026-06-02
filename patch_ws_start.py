with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

# 앱 시작시 웹소켓 백그라운드 스레드 자동 실행
ws_init = '''
# KIS WebSocket 백그라운드 자동 시작
import threading as _threading
def _start_ws():
    try:
        from kis_websocket import start_websocket
        # 코스피 주요 종목 기본 구독
        default_tickers = ["005930", "000660", "035720", "035420", "051910"]
        start_websocket(default_tickers)
    except Exception as e:
        print(f"WebSocket 시작 오류: {e}")

_ws_thread = _threading.Thread(target=_start_ws, daemon=True)
_ws_thread.start()
'''

# load_dotenv() 바로 다음에 삽입
content = content.replace('load_dotenv()\n', 'load_dotenv()\n' + ws_init)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)
print("✅ WebSocket 자동시작 패치 완료!")
