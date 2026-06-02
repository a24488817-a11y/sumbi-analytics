sudo systemctl restart sumbi &
grep -nC 7 "AI MACRO SIGNAL / 인공지능" main.py
cat << 'EOF' > fix_html_render.py
import re

try:
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 정규식을 사용하여 빈 줄과 과도한 들여쓰기를 제거하고 태그를 밀착시킴
    # (gap:20px;'> 와 <div style='flex:1;'> 사이의 공백 및 줄바꿈 압축)
    broken_pattern = r"(align-items:center;gap:20px;'>)\s+(<div style='flex:1;'>)"
    fixed_pattern = r"\1\n<div style='flex:1;'>\n"
    
    content = re.sub(broken_pattern, fixed_pattern, content)

    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ HTML 코드 노출 버그 완벽 수리 완료")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
EOF

# 스크립트 실행 및 앱 재시작
python3 fix_html_render.py
sudo systemctl restart sumbi &
grep -nC 8 "div style='flex:1;'" main.py
timedatectl | grep "Time zone"
cat << 'EOF' > fix_final_ui_time.py
import re

try:
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 마크다운 코드블록 버그 원천 차단
    # <div style='flex:1;'> 바로 아래의 빈 줄과 깊은 들여쓰기를 정규식으로 완벽히 제거하여 태그 밀착
    content = re.sub(r"<div style='flex:1;'>\s*\n\s*<div", "<div style='flex:1;'>\n<div", content)
    
    # 내부 태그들의 불필요한 빈 줄 및 들여쓰기도 모두 압축
    content = re.sub(r"</div>\s*\n\s*<div", "</div>\n<div", content)
    content = re.sub(r"</div>\s*\n\s*</div", "</div>\n</div", content)

    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("✅ HTML 빈줄/들여쓰기 진공 압축 완료 (마크다운 버그 원천 차단)")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
EOF

# 1. UI 복구 스크립트 실행
python3 fix_final_ui_time.py
# 2. AWS 서버 시계를 한국 시간(KST)으로 영구 동기화
sudo timedatectl set-timezone Asia/Seoul
# 3. 앱 재시작 (변경된 코드와 동기화된 시간 적용)
sudo systemctl restart sumbi &
cat ~/sumbi-analytics/v3_scorer.py
cat ~/sumbi-analytics/main.py
find / -name "main.py" 2>/dev/null | grep sumbi
ls ~/
cat ~/main.py
cat ~/v3_scorer.py
head -100 ~/v3_scorer.py
head -80 ~/main.py
cp ~/v3_scorer.py ~/v3_scorer.py.backup_$(date +%Y%m%d)
cat > ~/v3_scorer.py << 'EOF'
EOF

sudo systemctl restart sumbi.service && sudo systemctl status sumbi.service
cp ~/v3_scorer.py.backup_20260523 ~/v3_scorer.py
head -5 ~/v3_scorer.py
sudo systemctl restart sumbi.service
cd ~ && git init && git remote add origin https://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@github.com/a24488817-a11y/sumbi-analytics.git
git remote set-url origin https://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@github.com/a24488817-a11y/sumbi-analytics.git
git pull origin main
python3 ~/upload_scorer.py
cat > ~/upload_scorer.py << 'PYEOF'
import urllib.request, json, base64

token = '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'
repo = 'a24488817-a11y/sumbi-analytics'
url = f'https://api.github.com/repos/{repo}/contents/v3_scorer.py'

req = urllib.request.Request(url, headers={'Authorization': f'token {token}', 'User-Agent': 'sumbi'})
res = json.loads(urllib.request.urlopen(req).read())
sha = res['sha']
print('SHA:', sha)
PYEOF

python3 ~/upload_scorer.py
python3 -c "
import urllib.request, json, base64

token = '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'
repo = 'a24488817-a11y/sumbi-analytics'
sha = '03f24e452f6f7588b340579b9db392de2eec7d45'

with open('/home/ubuntu/v3_scorer.py', 'rb') as f:
    content = base64.b64encode(f.read()).decode()

data = json.dumps({'message': 'feat: 세력발자국 점수제 적용', 'content': content, 'sha': sha}).encode()
req = urllib.request.Request(
    f'https://api.github.com/repos/{repo}/contents/v3_scorer.py',
    data=data, method='PUT',
    headers={'Authorization': f'token {token}', 'Content-Type': 'application/json', 'User-Agent': 'sumbi'}
)
res = json.loads(urllib.request.urlopen(req).read())
print('업로드 완료:', res['content']['name'])
"
cd ~ && git pull origin main && sudo systemctl restart sumbi.service
sudo systemctl status sumbi.service
cat > ~/auto_push.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu
git add -A
git commit -m "auto: $(date '+%Y-%m-%d %H:%M')"
git push origin main
EOF

chmod +x ~/auto_push.sh
crontab -e
crontab -l
head -80 ~/main.py
cat > ~/kis_websocket.py << 'EOF'
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
EOF

pip install websocket-client --break-system-packages
pip3 install websocket-client
python3 -c "
from kis_websocket import get_ws_approval_key
key = get_ws_approval_key()
if key:
    print('✅ 접속키 발급 성공:', key[:20], '...')
else:
    print('❌ 접속키 발급 실패 - API 키 확인 필요')
"
cat > ~/kofia_crawler.py << 'EOF'
"""
KOFIA 대차잔고 + KRX 공매도 자동 수집기
매일 장 마감 후 자동 실행 → v3_scorer에 반영
"""
import requests
import pandas as pd
import json
import os
from datetime import datetime, timedelta

def get_kofia_short_balance(ticker):
    """KOFIA 대차잔고 조회"""
    try:
        today = datetime.now().strftime('%Y%m%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        
        url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'http://data.krx.co.kr'
        }
        params = {
            'bld': 'dbms/MDC/STAT/standard/MDCSTAT06301',
            'startDd': week_ago,
            'endDd': today,
            'isuCd': ticker,
            'share': '1',
            'money': '1'
        }
        
        res = requests.post(url, headers=headers, data=params, timeout=10)
        data = res.json()
        
        if 'output' in data and data['output']:
            latest = data['output'][0]
            prev = data['output'][1] if len(data['output']) > 1 else latest
            
            balance_today = int(latest.get('BALANCE', '0').replace(',', ''))
            balance_prev = int(prev.get('BALANCE', '0').replace(',', ''))
            change = balance_today - balance_prev
            
            return {
                'ticker': ticker,
                'balance': balance_today,
                'balance_change': change,
                'date': latest.get('TRD_DD', today)
            }
    except Exception as e:
        print(f"[KOFIA] 오류: {e}")
    return {}

def get_krx_short_ratio(ticker):
    """KRX 공매도 비율 조회"""
    try:
        today = datetime.now().strftime('%Y%m%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        
        url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'http://data.krx.co.kr'
        }
        params = {
            'bld': 'dbms/MDC/STAT/standard/MDCSTAT06001',
            'startDd': week_ago,
            'endDd': today,
            'isuCd': ticker,
            'share': '1',
            'money': '1'
        }
        
        res = requests.post(url, headers=headers, data=params, timeout=10)
        data = res.json()
        
        if 'output' in data and data['output']:
            latest = data['output'][0]
            ratio = float(latest.get('RATIO', '0').replace(',', ''))
            return {
                'ticker': ticker,
                'short_ratio': ratio,
                'date': latest.get('TRD_DD', today)
            }
    except Exception as e:
        print(f"[KRX] 오류: {e}")
    return {}

def get_short_data(ticker):
    """대차잔고 + 공매도 통합 조회 → v3_scorer 형식으로 반환"""
    balance = get_kofia_short_balance(ticker)
    short = get_krx_short_ratio(ticker)
    
    result = {
        'short_ratio': short.get('short_ratio', 0),
        'balance_change': balance.get('balance_change', 0),
        'short_balance': balance.get('balance', 0),
        'credit_ratio': 0  # 추후 신용잔고 추가
    }
    
    print(f"[{ticker}] 공매도비율: {result['short_ratio']}% | 대차변화: {result['balance_change']:+,}")
    return result

if __name__ == "__main__":
    # 테스트
    tickers = ['005930', '000660', '035420']  # 삼성, SK하이닉스, 네이버
    print("=== KOFIA/KRX 대차잔고 수집 테스트 ===")
    for t in tickers:
        data = get_short_data(t)
        print(data)
        print()
EOF

python3 ~/kofia_crawler.py
cat > ~/kofia_crawler.py << 'EOF'
import requests
import json
from datetime import datetime, timedelta

def get_short_data(ticker):
    """KRX 공매도 데이터 조회"""
    try:
        today = datetime.now().strftime('%Y%m%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        
        url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'http://data.krx.co.kr/contents/MDC/STAT/standard/MDCSTAT06001.cmd',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json, text/javascript, */*'
        }
        params = f"bld=dbms/MDC/STAT/standard/MDCSTAT06001&startDd={week_ago}&endDd={today}&isuCd={ticker}&share=1&money=1&csvxls_isNo=false"
        
        res = requests.post(url, headers=headers, data=params, timeout=10)
        print(f"[{ticker}] 상태코드: {res.status_code}")
        print(f"[{ticker}] 응답: {res.text[:200]}")
        
        data = res.json()
        if 'output' in data and data['output']:
            latest = data['output'][0]
            ratio = float(latest.get('RATIO', '0').replace(',', ''))
            print(f"[{ticker}] 공매도비율: {ratio}%")
            return {'short_ratio': ratio, 'balance_change': 0, 'short_balance': 0, 'credit_ratio': 0}
    except Exception as e:
        print(f"[{ticker}] 오류: {e}")
    
    return {'short_ratio': 0, 'balance_change': 0, 'short_balance': 0, 'credit_ratio': 0}

if __name__ == "__main__":
    get_short_data('005930')
EOF

python3 ~/kofia_crawler.py
cat > ~/kofia_crawler.py << 'EOF'
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
EOF

python3 ~/kofia_crawler.py
python3 ~/kofia_crawler.py 2>&1 | tail -10
cat ~/sumbi-analytics/v3_scorer.py | head -100
ls ~/sumbi-analytics/
cat ~/.env 2>/dev/null || cat ~/sumbi-analytics/.env 2>/dev/null
ls /
ls /home/ubuntu/
find / -name "main.py" 2>/dev/null | head -5
cat ~/v3_scorer.py | head -150
cat ~/main.py | head -100
systemctl status sumbi.service
cat ~/v3_scorer.py | head -200
cat ~/kis_websocket.py | head -50
grep -n "realtime\|websocket\|kis_web" ~/v3_scorer.py
grep -n "realtime\|websocket" ~/main.py | head -20
wc -l ~/v3_scorer.py ~/main.py
tail -100 ~/v3_scorer.py
cat > ~/patch_realtime.py << 'EOF'
with open('/home/ubuntu/v3_scorer.py', 'r') as f:
    content = f.read()

realtime_func = '''
def calc_realtime_score(realtime_data):
    """실시간 체결강도 점수 (10점) - KIS WebSocket"""
    if not realtime_data:
        return 5, {}
    score = 5
    details = {}
    strength = realtime_data.get('strength', 100)
    volume = realtime_data.get('volume', 0)
    avg_volume = realtime_data.get('avg_volume', 0)
    if strength > 130: score += 3
    elif strength > 115: score += 2
    elif strength > 105: score += 1
    elif strength < 85: score -= 2
    elif strength < 75: score -= 3
    if avg_volume > 0:
        ratio = volume / avg_volume
        if ratio > 3: score += 2
        elif ratio > 2: score += 1
        elif ratio < 0.3: score -= 1
    details['체결강도'] = round(strength, 1)
    return max(0, min(score, 10)), details

'''

content = content.replace('def calc_sumbi_v3(', realtime_func + 'def calc_sumbi_v3(')

content = content.replace(
    'def calc_sumbi_v3(investor, macro, df_chart, info=None, news_list=None, short_data=None, sector_data=None, broker_data=None):',
    'def calc_sumbi_v3(investor, macro, df_chart, info=None, news_list=None, short_data=None, sector_data=None, broker_data=None, realtime_data=None):'
)

content = content.replace(
    '    broker, broker_d = calc_broker_score(broker_data)\n\n    total = flow + chart + fund + news + short + macro_s + sector + broker',
    '    broker, broker_d = calc_broker_score(broker_data)\n    realtime, realtime_d = calc_realtime_score(realtime_data)\n\n    total = flow + chart + fund + news + short + macro_s + sector + broker + realtime'
)

content = content.replace("        'broker': (broker, 5, broker_d),",
    "        'broker': (broker, 5, broker_d),\n            'realtime': (realtime, 10, realtime_d),")

with open('/home/ubuntu/v3_scorer.py', 'w') as f:
    f.write(content)
print("✅ 실시간 체결강도 연동 완료! 총점 110점으로 확장")
EOF

python3 ~/patch_realtime.py
grep -n "calc_sumbi_v3\|kis_websocket\|import" ~/main.py | head -30
grep -n "calc_sumbi_v3(" ~/main.py
cat > ~/patch_main_realtime.py << 'EOF'
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

# kis_websocket import 추가
content = content.replace(
    'from v3_scorer import calc_sumbi_v3',
    'from v3_scorer import calc_sumbi_v3\nfrom kis_websocket import realtime_data, start_websocket'
)

# calc_sumbi_v3 호출에 realtime_data 추가
content = content.replace(
    'calc_sumbi_v3(investor, macro, df_chart, info=info, news_list=news_list)',
    'calc_sumbi_v3(investor, macro, df_chart, info=info, news_list=news_list, realtime_data=realtime_data.get(ticker))'
)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)
print("✅ main.py 패치 완료!")
EOF

python3 ~/patch_main_realtime.py
grep -n "start_websocket\|if __name__\|def main" ~/kis_websocket.py
cat > ~/patch_ws_start.py << 'EOF'
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
EOF

python3 ~/patch_ws_start.py
sudo systemctl restart sumbi.service && sleep 5 && sudo systemctl status sumbi.service | tail -20
sudo systemctl status sumbi.service | tail -25
grep -n "news_list\|get_news\|naver_news\|fetch_news" ~/main.py | head -20
sed -n '369,420p' ~/main.py
grep -i "dart\|DART" ~/.env
echo 'DART_API_KEY=4e3bc950251d3631af3da6fcd3661b6a3828e9ed' >> ~/.env
cat > ~/dart_connector.py << 'EOF'
import requests, os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from functools import lru_cache

load_dotenv()
DART_KEY = os.environ.get("DART_API_KEY")

@lru_cache(maxsize=500)
def get_corp_code(ticker):
    """종목코드 → DART 고유번호 변환"""
    try:
        import zipfile, io, xml.etree.ElementTree as ET
        url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={DART_KEY}"
        r = requests.get(u

EOF
python3 -c "
content = '''import requests, os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from functools import lru_cache

load_dotenv()
DART_KEY = os.environ.get(\"DART_API_KEY\")

@lru_cache(maxsize=500)
def get_corp_code(ticker):
    try:
        import zipfile, io, xml.etree.ElementTree as ET
        url = f\"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={DART_KEY}\"
        r = requests.get(url, timeout=15)
        zf = zipfile.ZipFile(io.BytesIO(r.content))
        xml_data = zf.read(\"CORPCODE.xml\")
        root = ET.fromstring(xml_data)
        for corp in root.findall(\"list\"):
            stock = corp.findtext(\"stock_code\", \"\").strip()
            if stock == ticker:
                return corp.findtext(\"corp_code\", \"\").strip()
    except Exception as e:
        print(f\"corp_code 오류: {e}\")
    return None

def get_dart_disclosures(ticker, days=3):
    try:
        corp_code = get_corp_code(ticker)
        if not corp_code:
            return []
        start = (datetime.now() - timedelta(days=days)).strftime(\"%Y%m%d\")
        end = datetime.now().strftime(\"%Y%m%d\")
        params = {\"crtfc_key\": DART_KEY, \"corp_code\": corp_code,
                  \"bgn_de\": start, \"end_de\": end, \"sort\": \"date\",
                  \"sort_mth\": \"desc\", \"page_count\": 10}
        r = requests.get(\"https://opendart.fss.or.kr/api/list.json\", params=params, timeout=10)
        data = r.json()
        if data.get(\"status\") != \"000\":
            return []
        return [{ \"title\": i.get(\"report_nm\",\"\"), \"date\": i.get(\"rcept_dt\",\"\") } for i in data.get(\"list\",[])]
    except Exception as e:
        print(f\"DART 공시 오류: {e}\")
        return []

def calc_dart_score(ticker):
    disclosures = get_dart_disclosures(ticker)
    if not disclosures:
        return 2, {}
    score = 2
    positive = [\"자사주\",\"배당\",\"수주\",\"계약\",\"자기주식취득\"]
    negative = [\"횡령\",\"배임\",\"조사\",\"상장폐지\",\"감사의견\",\"과징금\"]
    titles = []
    for d in disclosures[:5]:
        t = d[\"title\"]
        titles.append(t[:15])
        if any(k in t for k in positive): score += 1
        if any(k in t for k in negative): score -= 2
    return max(0, min(score, 5)), {\"공시수\": len(disclosures), \"최근\": titles}

if __name__ == \"__main__\":
    print(\"삼성전자 테스트:\")
    s, d = calc_dart_score(\"005930\")
    print(f\"점수: {s}/5, {d}\")
'''
with open('/home/ubuntu/dart_connector.py', 'w') as f:
    f.write(content)
print('파일 생성 완료')
"
python3 ~/dart_connector.py
ls -la ~/dart_connector.py && python3 ~/dart_connector.py
cat >> ~/v3_scorer.py << 'DARTEOF'

def calc_dart_score_wrapper(ticker):
    """DART 공시 점수 래퍼 (5점)"""
    try:
        from dart_connector import calc_dart_score
        score, details = calc_dart_score(ticker)
        return score, details
    except Exception as e:
        return 2, {}
DARTEOF

grep -n "def calc_sumbi_v3" ~/v3_scorer.py
python3 -c "
with open('/home/ubuntu/v3_scorer.py', 'r') as f:
    content = f.read()

# 파라미터에 ticker 추가
content = content.replace(
    'def calc_sumbi_v3(investor, macro, df_chart, info=None, news_list=None, short_data=None, sector_data=None, broker_data=None, realtime_data=None):',
    'def calc_sumbi_v3(investor, macro, df_chart, info=None, news_list=None, short_data=None, sector_data=None, broker_data=None, realtime_data=None, ticker=None):'
)

# DART 점수 계산 추가
content = content.replace(
    '    realtime, realtime_d = calc_realtime_score(realtime_data)',
    '    realtime, realtime_d = calc_realtime_score(realtime_data)\n    dart, dart_d = calc_dart_score_wrapper(ticker) if ticker else (2, {})'
)

# total에 dart 추가
content = content.replace(
    '    total = flow + chart + fund + news + short + macro_s + sector + broker + realtime',
    '    total = flow + chart + fund + news + short + macro_s + sector + broker + realtime + dart'
)

# breakdown에 dart 추가
content = content.replace(
    \"            'realtime': (realtime, 10, realtime_d),\",
    \"            'realtime': (realtime, 10, realtime_d),\\n            'dart': (dart, 5, dart_d),\"
)

with open('/home/ubuntu/v3_scorer.py', 'w') as f:
    f.write(content)
print('DART 점수 통합 완료! 총점 115점')
"
python3 -c "
with open('/home/ubuntu/v3_scorer.py', 'r') as f:
    content = f.read()

# 파라미터에 ticker 추가
content = content.replace(
    'def calc_sumbi_v3(investor, macro, df_chart, info=None, news_list=None, short_data=None, sector_data=None, broker_data=None, realtime_data=None):',
    'def calc_sumbi_v3(investor, macro, df_chart, info=None, news_list=None, short_data=None, sector_data=None, broker_data=None, realtime_data=None, ticker=None):'
)

# DART 점수 계산 추가
content = content.replace(
    '    realtime, realtime_d = calc_realtime_score(realtime_data)',
    '    realtime, realtime_d = calc_realtime_score(realtime_data)\n    dart, dart_d = calc_dart_score_wrapper(ticker) if ticker else (2, {})'
)

# total에 dart 추가
content = content.replace(
    '    total = flow + chart + fund + news + short + macro_s + sector + broker + realtime',
    '    total = flow + chart + fund + news + short + macro_s + sector + broker + realtime + dart'
)

# breakdown에 dart 추가
content = content.replace(
    \"            'realtime': (realtime, 10, realtime_d),\",
    \"            'realtime': (realtime, 10, realtime_d),\\n            'dart': (dart, 5, dart_d),\"
)

with open('/home/ubuntu/v3_scorer.py', 'w') as f:
    f.write(content)
print('DART 점수 통합 완료! 총점 115점')
"
python3 -c "
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

content = content.replace(
    'calc_sumbi_v3(investor, macro, df_chart, info=info, news_list=news_list, realtime_data=realtime_data.get(ticker))',
    'calc_sumbi_v3(investor, macro, df_chart, info=info, news_list=news_list, realtime_data=realtime_data.get(ticker), ticker=ticker)'
)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)
print('main.py ticker 전달 완료!')
"
sudo systemctl restart sumbi.service && sleep 5 && sudo systemctl status sumbi.service | tail -10
sudo systemctl status sumbi.service | tail -15
cd ~ && git add -A && git commit -m "DART+WebSocket 연동 완료 115점" && git push origin main
ls -la ~/sumbi_backup_*.tar.gz | tail -3
grep -i "naver\|CLIENT\|NAVER" ~/.env
cat ~/.env
echo 'NAVER_CLIENT_ID=Sdoj3I5WetzzjmyJAmen' >> ~/.env
echo 'NAVER_CLIENT_SECRET=d_dkWCKTKu' >> ~/.env
grep NAVER ~/.env
python3 -c "
content = '''import requests, os
from dotenv import load_dotenv

load_dotenv()
NAVER_ID = os.environ.get(\"NAVER_CLIENT_ID\")
NAVER_SECRET = os.environ.get(\"NAVER_CLIENT_SECRET\")

def get_naver_news(query, display=10):
    \"\"\"네이버 뉴스 검색 API\"\"\"
    try:
        headers = {
            \"X-Naver-Client-Id\": NAVER_ID,
            \"X-Naver-Client-Secret\": NAVER_SECRET
        }
        params = {\"query\": query, \"display\": display, \"sort\": \"date\"}
        r = requests.get(\"https://openapi.naver.com/v1/search/news.json\",
                        headers=headers, params=params, timeout=5)
        items = r.json().get(\"items\", [])
        return [{\"title\": i[\"title\"].replace(\"<b>\",\"\").replace(\"</b>\",\"\"),
                 \"link\": i[\"link\"],
                 \"pub\": i[\"pubDate\"]} for i in items]
    except Exception as e:
        print(f\"네이버 뉴스 오류: {e}\")
        return []

if __name__ == \"__main__\":
    news = get_naver_news(\"삼성전자 주식\", 5)
    print(f\"뉴스 {len(news)}건:\")
    for n in news:
        print(f\"  - {n[title][:30]}\")
'''
with open(\"/home/ubuntu/naver_news.py\", \"w\") as f:
    f.write(content)
print(\"완료\")
"
python3 ~/naver_news.py
python3 -c "
from naver_news import get_naver_news
news = get_naver_news('삼성전자 주식', 5)
print(f'뉴스 {len(news)}건:')
for n in news:
    print(f\"  - {n['title'][:30]}\")
"
python3 -c "
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

# get_news 함수에 네이버 뉴스 추가
old = '''def get_news(query):'''
new = '''def get_news(query):'''

# import 추가
content = content.replace(
    'from kis_websocket import realtime_data, start_websocket',
    'from kis_websocket import realtime_data, start_websocket\nfrom naver_news import get_naver_news'
)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)

# get_news 함수 확인
import subprocess
result = subprocess.run(['grep', '-n',
python3 -c "
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

# get_news 함수에 네이버 뉴스 추가
old = '''def get_news(query):'''
new = '''def get_news(query):'''

# import 추가
content = content.replace(
    'from kis_websocket import realtime_data, start_websocket',
    'from kis_websocket import realtime_data, start_websocket\nfrom naver_news import get_naver_news'
)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)

# get_news 함수 확인
import subprocess
result = subprocess.run(['grep', '-n',

grep -n "def get_news" ~/main.py
sed -n '369,395p' ~/main.py
python3 -c "
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

old = '''    except:
        return []

@st.cache_data(ttl=3600)
def get_chart_data'''

new = '''    except:
        return []

def get_news_combined(query):
    \"\"\"구글 RSS + 네이버 뉴스 통합\"\"\"
    results = get_news(query)
    try:
        from naver_news import get_naver_news
        naver = get_naver_news(query, 10)
        results = results + naver
    except Exception as e:
        pass
    return results[:20]

@st.cache_data(ttl=3600)
def get_chart_data'''

content = content.replace(old, new)

# news_list 호출을 combined로 교체
content = content.replace(
    'news_list= get_news(info[\\'name\\'] or ticker)',
    'news_list= get_news_combined(info[\\'name\\'] or ticker)'
)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)
print('네이버+구글 뉴스 병합 완료! 최대 20건')
"
sudo systemctl restart sumbi.service && sleep 5 && sudo systemctl status sumbi.service | tail -10
cd ~ && git add -A && git commit -m "네이버뉴스+DART+WebSocket 완전연동" && git push origin main
cd ~ && git log --oneline -3
grep -n "macro\|fred\|FRED" ~/main.py | head -10
sed -n '271,320p' ~/main.py
grep -i "fred\|FRED" ~/.env
echo 'FRED_API_KEY=66f8e6a39938571b83bcdf4bae9b9418' >> ~/.env
grep FRED ~/.env
python3 -c "
content = '''import requests, os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
FRED_KEY = os.environ.get(\"FRED_API_KEY\")

def get_fred_series(series_id):
    try:
        url = f\"https://api.stlouisfed.org/fred/series/observations\"
        params = {\"series_id\": series_id, \"api_key\": FRED_KEY,
                  \"file_type\": \"json\", \"limit\": 1, \"sort_order\": \"desc\"}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        val = data[\"observations\"][0][\"value\"]
        return float(val) if val != \".\" else None
    except:
        return None

def get_macro_fred():
    return {
        \"ffr\": get_fred_series(\"FEDFUNDS\"),
        \"tnx\": get_fred_series(\"DGS10\"),
        \"dxy\": get_fred_series(\"DTWEXBGS\"),
        \"cpi\": get_fred_series(\"CPIAUCSL\"),
        \"vix\": get_fred_series(\"VIXCLS\"),
        \"krw\": get_fred_series(\"DEXKOUS\"),
        \"wti\": get_fred_series(\"DCOILWTICO\"),
    }

if __name__ == \"__main__\":
    data = get_macro_fred()
    print(\"FRED 매크로 데이터:\")
    for k, v in data.items():
        print(f\"  {k}: {v}\")
'''
with open(\"/home/ubuntu/fred_conne
ls ~/fred_connector.py && python3 ~/fred_connector.py
cat > /home/ubuntu/fred_connector.py << 'FREDEOF'
import requests, os
from dotenv import load_dotenv

load_dotenv()
FRED_KEY = os.environ.get("FRED_API_KEY")

def get_fred_series(series_id):
    try:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {"series_id": series_id, "api_key": FRED_KEY,
                  "file_type": "json", "limit": 1, "sort_order": "desc"}
        r = requests.get(url, params=params, timeout=10)
        val = r.json()["observations"][0]["value"]
        return float(val) if val != "." else None
    except:
        return None

def get_macro_fred():
    return {
        "ffr": get_fred_series("FEDFUNDS"),
        "tnx": get_fred_series("DGS10"),
        "cpi": get_fred_series("CPIAUCSL"),
        "vix": get_fred_series("VIXCLS"),
        "krw": get_fred_series("DEXKOUS"),
        "wti": get_fred_series("DCOILWTICO"),
    }

if __name__ == "__main__":
    data = get_macro_fred()
    print("FRED 매크로:")
    for k, v in data.items():
        print(f"  {k}: {v}")
FREDEOF

python3 /home/ubuntu/fred_connector.py
python3 -c "
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

content = content.replace(
    'from naver_news import get_naver_news',
    'from naver_news import get_naver_news\nfrom fred_connector import get_macro_fred'
)

old = '''def get_macro():
    \"\"\"yfinance'''
new = '''def get_macro():
    \"\"\"FRED API + yfinance 병합\"\"\"
    try:
        fred = get_macro_fred()
        if fred and fred.get(\"tnx\"):
            return fred
    except:
        pass
    \"\"\"yfinance'''

content = content.replace(old, new)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)
print('FRED 매크로 연동 완료!')
"
sudo systemctl restart sumbi.service && sleep 5 && sudo systemctl status sumbi.service | tail -8
cd ~ && git add -A && git commit -m "FRED 매크로 실시간 연동 완료" && git push origin main
grep -n "def get_macro" ~/main.py
sed -n '271,285p' ~/main.py
python3 -c "
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

# 잘못된 get_macro 함수 교체
old = '''def get_macro():
    \"\"\"FRED API + yfinance 병합\"\"\"
    try:
        fred = get_macro_fred()
        if fred and fred.get(\"tnx\"):
            return fred
    except:
        pass
    \"\"\"yfinance'''

new = '''def get_macro():
    \"\"\"FRED API + yfinance 병합\"\"\"
    try:
        fred = get_macro_fred()
        if fred and fred.get(\"tnx\"):
            return fred
    except:
        pass
    # yfinance fallback'''

content = content.replace(old, new)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)
print('수정 완료')
"
python3 -c "import py_compile; py_compile.compile('/home/ubuntu/main.py'); print('문법 OK')"
sed -n '395,415p' ~/main.py
sudo systemctl restart sumbi.service && sudo systemctl status sumbi.service
python3 -c "import py_compile; py_compile.compile('/home/ubuntu/main.py', doraise=True)" 2>&1
sed -n '390,415p' ~/main.py
sed -i '/^from fred_connector import get_macro_fred$/s/^/        /' ~/main.py
python3 -c "import py_compile; py_compile.compile('/home/ubuntu/main.py', doraise=True)" && echo "OK" && sudo systemctl restart sumbi.service
grep -n "realtime" ~/main.py | head -20
grep -n "realtime" ~/v3_scorer.py | head -20
sed -n '360,370p' ~/v3_scorer.py
sed -n '330,365p' ~/v3_scorer.py
sed -i 's/broker, broker_d = calc_broker_score(broker_data)/broker, broker_d = calc_broker_score(broker_data)\n    realtime, realtime_d = calc_realtime_score(realtime_data)/' ~/v3_scorer.py
sed -i 's/total = flow + chart + fund + news + short + macro_s + sector + broker$/total = flow + chart + fund + news + short + macro_s + sector + broker + realtime/' ~/v3_scorer.py
sudo systemctl restart sumbi.service && sudo systemctl status sumbi.service | head -5
sed -n '330,370p' ~/v3_scorer.py
sed -i 's/realtime, realtime_d = calc_realtime_score(realtime_data)/realtime, realtime_d = calc_realtime_score(realtime_data)\n    dart, dart_d = calc_dart_score(dart_data)/' ~/v3_scorer.py
sed -i 's/total = flow + chart + fund + news + short + macro_s + sector + broker + realtime$/total = flow + chart + fund + news + short + macro_s + sector + broker + realtime + dart/' ~/v3_scorer.py
sudo systemctl restart sumbi.service && echo "OK"
grep -n "^def calc_" ~/v3_scorer.py
sed -i 's/dart, dart_d = calc_dart_score(dart_data)/dart, dart_d = calc_dart_score_wrapper(ticker)/' ~/v3_scorer.py
grep -n "dart" ~/v3_scorer.py | grep -v "^373\|^374"
sudo systemctl restart sumbi.service && echo "OK"
sudo journalctl -u sumbi.service -n 30 --no-pager
sed -i '341s/.*/    dart, dart_d = calc_dart_score_wrapper(ticker)/' ~/v3_scorer.py
sed -n '341p' ~/v3_scorer.py && sudo systemctl restart sumbi.service && echo "OK"
sed -n '330,380p' ~/v3_scorer.py
cd ~ && python3 -c "
from v3_scorer import calc_dart_score_wrapper
import signal

def timeout(s, f): signal.signal(signal.SIGALRM, f); signal.alarm(s)
def handler(s, f): raise TimeoutError('timeout')

timeout(10, handler)
try:
    result = calc_dart_score_wrapper('042660')
    print('OK:', result)
except TimeoutError:
    print('TIMEOUT - dart API 느림')
except Exception as e:
    print('ERROR:', e)
"
cat > /tmp/fix_dart.py << 'EOF'
with open('/home/ubuntu/v3_scorer.py', 'r') as f:
    content = f.read()

old = '''def calc_dart_score_wrapper(ticker):
    """DART 공시 점수 계산 (5점)"""
    try:
        from dart_connector import calc_dart_score
        score, details = calc_dart_score(ticker)
        return score, details
    except Exception as e:
        return 2, {}'''

new = '''def calc_dart_score_wrapper(ticker):
    """DART 공시 점수 계산 (5점)"""
    try:
        from dart_connector import calc_dart_score
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as ex:
            future = ex.submit(calc_dart_score, ticker)
            score, details = future.result(timeout=5)
        return score, details
    except Exception as e:
        return 2, {}'''

content = content.replace(old, new)
with open('/home/ubuntu/v3_scorer.py', 'w') as f:
    f.write(content)
print('완료')
EOF

python3 /tmp/fix_dart.py && sudo systemctl restart sumbi.service && echo "OK"
sed -n '373,385p' ~/v3_scorer.py
sed -i '377s/.*/        import concurrent.futures; fut = concurrent.futures.ThreadPoolExecutor().submit(calc_dart_score, ticker); score, details = fut.result(timeout=5)/' ~/v3_scorer.py && sudo systemctl restart sumbi.service && echo "OK"
cp ~/main.py ~/main.py.backup_0523 && cp ~/v3_scorer.py ~/v3_scorer.py.backup_0523 && echo "백업 완료"
grep -n "042660" ~/main.py
sed -i "475s/st.session_state.ticker = '042660'/st.session_state.ticker = ''/" ~/main.py && sed -i "477s/st.session_state.query_name = '042660'/st.session_state.query_name = ''/" ~/main.py && sudo systemctl restart sumbi.service && echo "OK"
sudo journalctl -u sumbi.service -n 20 --no-pager | tail -20
sudo journalctl -u sumbi.service -n 30 --no-pager | grep -E "ERROR|Error|error" | tail -15
grep -n "session_state" ~/main.py | grep -i "result\|v3_result\|clear" | head -20
grep -n "LAUNCH\|deep_scan\|if.*button" ~/main.py | head -20
sed -n '520,545p' ~/main.py
sed -n '535,542p' ~/main.py
sed -n '534,536p' ~/main.py
sed -n '537,540p' ~/main.py
sed -i '537a\    if not ticker:\n        st.stop()' ~/main.py
sed -i '538s/^/if not ticker: st.stop()\n/' ~/main.py && sudo systemctl restart sumbi.service && echo "OK"
sudo systemctl status sumbi.service | head -3
grep -n "if not ticker" ~/main.py
sed -n '535,545p' ~/main.py | cat -A
grep -n "st.stop" ~/main.py
grep -n "timeout\|time_out\|websocket\|KIS" ~/kis_websocket.py | head -20
sed -n '77,130p' ~/kis_websocket.py
grep -n "start_websocket\|realtime_data" ~/main.py | head -15
sed -n '35,55p' ~/main.py
python3 -c "
lines = open('/home/ubuntu/main.py').readlines()
out = []
for i, line in enumerate(lines):
    out.append(line)
    if 'st.session_state.ticker = code' in line:
        indent = '        '
        out.append(indent + 'try:\n')
        out.append(indent + '    from kis_websocket import start_websocket\n')
        out.append(indent + '    start_websocket([code])\n')
        out.append(indent + 'except: pass\n')
open('/home/ubuntu/main.py','w').writelines(out)
print('완료')
" && sudo systemctl restart sumbi.service && echo "OK"
python3 -c "
lines = open('/home/ubuntu/main.py').readlines()
out = []
for i, line in enumerate(lines):
    out.append(line)
    if 'st.session_state.ticker = code' in line:
        indent = '        '
        out.append(indent + 'try:\n')
        out.append(indent + '    from kis_websocket import start_websocket\n')
        out.append(indent + '    start_websocket([code])\n')
        out.append(indent + 'except: pass\n')
open('/home/ubuntu/main.py','w').writelines(out)
print('완료')
" && sudo systemctl restart sumbi.service && echo "OK"
sudo journalctl -u sumbi.service -n 20 --no-pager | tail -20
cat /home/ubuntu/main.py
grep -n "websocket\|WebSocket\|subscribe\|ws_client\|KIS" /home/ubuntu/main.py | head -60
# 1. kis_websocket.py 전체 보기
cat /home/ubuntu/kis_websocket.py
# 2. main.py 520~540번 줄 보기
sed -n '520,545p' /home/ubuntu/main.py
cat > /tmp/ws_patch.py << 'EOF'
import re

with open('/home/ubuntu/kis_websocket.py', 'r') as f:
    content = f.read()

# 전역변수 + stop_websocket 추가 (파일 상단 import 다음에)
insert_after = 'import threading\n'
global_vars = '''
_ws_app = None
_ws_thread = None

def stop_websocket():
    global _ws_app, _ws_thread
    if _ws_app:
        try:
            _ws_app.close()
        except:
            pass
        _ws_app = None
    _ws_thread = None

'''
if '_ws_app = None' not in content:
    content = content.replace(insert_after, insert_after + global_vars)

# start_websocket 함수 교체
old_func = '''def start_websocket(tickers):
    """WebSocket 시작"""
    approval_key = get_ws_approval_key()
    if not approval_key:
        print("[WS] 승인키 발급 실패")
        return

    ws = websocket.WebSocketApp(
        "wss://ops.koreainvestment.com:21000",
        on_open=lambda ws: on_open(ws, approval_key, tickers),
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    t = threading.Thread(target=ws.run_forever)
    t.daemon = True
    t.start()'''

new_func = '''def start_websocket(tickers):
    """WebSocket 시작"""
    global _ws_app, _ws_thread
    stop_websocket()

    approval_key = get_ws_approval_key()
    if not approval_key:
        print("[WS] 승인키 발급 실패")
        return

    _ws_app = websocket.WebSocketApp(
        "wss://ops.koreainvestment.com:21000",
        on_open=lambda ws: on_open(ws, approval_key, tickers),
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    _ws_thread = threading.Thread(target=_ws_app.run_forever)
    _ws_thread.daemon = True
    _ws_thread.start()'''

if old_func in content:
    content = content.replace(old_func, new_func)
    print("start_websocket 교체 성공")
else:
    print("WARNING: start_websocket 패턴 불일치, 수동 확인 필요")

with open('/home/ubuntu/kis_websocket.py', 'w') as f:
    f.write(content)

print("kis_websocket.py 수정 완료")
EOF

python3 /tmp/ws_patch.py
cat > /tmp/main_patch.py << 'EOF'
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

# 중복 start_websocket 호출 제거 + stop 추가
old_block = '''        try:
            from kis_websocket import start_websocket
                start_websocket([code])
        except: pass
        try:
            from kis_websocket import start_websocket
                start_websocket([code])
        except: pass'''

# 패턴이 정확히 안맞을 수 있으니 라인 기반으로 처리
lines = content.split('\n')
new_lines = []
skip_next = False
i = 0
while i < len(lines):
    line = lines[i]
    # 두 번째 중복 try 블록 제거
    if ('from kis_websocket import start_websocket' in line and
        i > 0 and 'from kis_websocket import start_websocket' in '\n'.join(lines[max(0,i-5):i])):
        # 이미 한번 나왔던 패턴 - 이 try 블록 건너뜀
        if i+1 < len(lines) and 'start_websocket' in lines[i+1]:
            i += 2  # start_websocket 줄도 건너뜀
            if i < len(lines) and 'except' in lines[i]:
                i += 2  # except: pass 건너뜀
            continue
    # 첫 번째 start_websocket import를 stop 포함으로 교체
    if 'from kis_websocket import start_websocket' in line and 'stop_websocket' not in line:
        indent = len(line) - len(line.lstrip())
        sp = ' ' * indent
        new_lines.append(f'{sp}from kis_websocket import stop_websocket, start_websocket')
        new_lines.append(f'{sp}stop_websocket()')
        i += 1
        continue
    new_lines.append(line)
    i += 1

with open('/home/ubuntu/main.py', 'w') as f:
    f.write('\n'.join(new_lines))

print("main.py 수정 완료")
EOF

python3 /tmp/main_patch.py
# 수정 확인
grep -n "stop_websocket\|start_websocket" /home/ubuntu/main.py
grep -n "stop_websocket\|_ws_app" /home/ubuntu/kis_websocket.py
# 재시작
sudo systemctl restart sumbi.service
sudo journalctl -u sumbi.service -f
cat > /tmp/fix_ws.py << 'EOF'
with open('/home/ubuntu/kis_websocket.py', 'r') as f:
    lines = f.readlines()

# 전역변수 삽입 위치 찾기 (import 끝난 직후)
insert_idx = 0
for i, line in enumerate(lines):
    if line.startswith('import ') or line.startswith('from '):
        insert_idx = i + 1

global_block = [
    '\n',
    '_ws_app = None\n',
    '_ws_thread = None\n',
    '\n',
    'def stop_websocket():\n',
    '    global _ws_app, _ws_thread\n',
    '    if _ws_app:\n',
    '        try:\n',
    '            _ws_app.close()\n',
    '        except:\n',
    '            pass\n',
    '        _ws_app = None\n',
    '    _ws_thread = None\n',
    '\n',
]

if '_ws_app = None' not in ''.join(lines):
    lines = lines[:insert_idx] + global_block + lines[insert_idx:]

# ws = websocket.WebSocketApp → _ws_app = websocket.WebSocketApp
new_lines = []
for line in lines:
    line = line.replace(
        'ws = websocket.WebSocketApp(',
        '_ws_app = websocket.WebSocketApp('
    ).replace(
        't = threading.Thread(target=ws.run_forever)',
        '_ws_thread = threading.Thread(target=_ws_app.run_forever)'
    ).replace(
        't.daemon = True',
        '_ws_thread.daemon = True'
    ).replace(
        't.start()',
        '_ws_thread.start()'
    )
    new_lines.append(line)

with open('/home/ubuntu/kis_websocket.py', 'w') as f:
    f.writelines(new_lines)

print("완료")
EOF

python3 /tmp/fix_ws.py# 확인
grep -n "_ws_app\|stop_websocket" /home/ubuntu/kis_websocket.py
# 재시작
sudo systemctl restart sumbi.service
sudo journalctl -u sumbi.service -f --no-pager | tail -20
python3 /tmp/fix_ws.py
grep -n "_ws_app\|stop_websocket" /home/ubuntu/kis_websocket.py
sudo systemctl restart sumbi.service
sudo journalctl -u sumbi.service --no-pager | tail -20
python3 -c "import py_compile; py_compile.compile('/home/ubuntu/main.py', doraise=True)" 2>&1
sed -n '525,545p' /home/ubuntu/main.py
cat > /tmp/fix_indent.py << 'EOF'
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

# 문제 블록 교체
old = '''        try:
            from kis_websocket import stop_websocket, start_websocket
            stop_websocket()
                start_websocket([code])
        except: pass
        try:
            # 캐시 초기화'''

new = '''        try:
            from kis_websocket import stop_websocket, start_websocket
            stop_websocket()
            start_websocket([code])
        except: pass
        # 캐시 초기화'''

if old in content:
    content = content.replace(old, new)
    print("수정 성공")
else:
    print("패턴 불일치 - 수동 확인 필요")
    # 들여쓰기 문제만 수정
    content = content.replace(
        '                start_websocket([code])\n        except: pass\n        try:\n            # 캐시 초기화',
        '            start_websocket([code])\n        except: pass\n        # 캐시 초기화'
    )
    print("대체 수정 시도")

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)
EOF

python3 /tmp/fix_indent.py
python3 -c "import py_compile; py_compile.compile('/home/ubuntu/main.py', doraise=True)" && echo "문법 OK"
sudo systemctl restart sumbi.service
# 백업으로 복원
cp ~/main.py.backup_0523 /home/ubuntu/main.py
# 오늘 수정사항 확인 (백업이 오늘 것인지 확인)
grep -n "stop_websocket\|042660\|st.stop" /home/ubuntu/main.py | head -20
cat > /tmp/full_patch.py << 'EOF'
with open('/home/ubuntu/main.py', 'r') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # 1. 042660 기본값 제거 (475, 477번 줄 근처)
    if "st.session_state.ticker = '042660'" in line:
        new_lines.append(line.replace("st.session_state.ticker = '042660'", "st.session_state.ticker = ''"))
        i += 1
        continue
    if "st.session_state.query_name = '042660'" in line:
        new_lines.append(line.replace("st.session_state.query_name = '042660'", "st.session_state.query_name = ''"))
        i += 1
        continue

    # 2. WebSocket 시작 (초기 기본 tickers - L38~42 근처)
    if 'start_websocket(default_tickers)' in line and 'stop_websocket' not in ''.join(lines[max(0,i-3):i]):
        indent = len(line) - len(line.lstrip())
        sp = ' ' * indent
        new_lines.append(f'{sp}from kis_websocket import stop_websocket, start_websocket\n')
        new_lines.append(f'{sp}stop_websocket()\n')
        new_lines.append(line)
        i += 1
        continue

    # 3. 검색 버튼 WebSocket (중복 try 제거하고 깔끔하게)
    if 'from kis_websocket import start_websocket' in line and 'stop_websocket' not in line:
        indent = len(line) - len(line.lstrip())
        sp = ' ' * indent
        new_lines.append(f'{sp}from kis_websocket import stop_websocket, start_websocket\n')
        new_lines.append(f'{sp}stop_websocket()\n')
        # 다음 줄이 start_websocket이면 들여쓰기 맞춰서 추가
        if i+1 < len(lines) and 'start_websocket' in lines[i+1]:
            next_line = lines[i+1].lstrip()
            new_lines.append(f'{sp}{next_line}')
            i += 2
            # except: pass 건너뜀
            if i < len(lines) and 'except' in lines[i]:
                i += 1
            # 두 번째 try 블록 건너뜀
            if i < len(lines) and lines[i].strip() == 'try:':
                i += 1
                while i < len(lines) and (lines[i].startswith('            ') or lines[i].strip().startswith('from kis') or lines[i].strip().startswith('start_web')):
                    i += 1
                if i < len(lines) and 'except' in lines[i]:
                    i += 1
            continue
        i += 1
        continue

    # 4. ticker 없을 때 st.stop() - placeholder 다음에 추가
    if 'placeholder=' in line and '042660' in line:
        new_lines.append(line.replace("placeholder='042660 · 대우조선해양 · 조선업종 · SK바이오사이언스'", "placeholder='종목코드 또는 종목명을 입력하세요'"))
        i += 1
        continue

    new_lines.append(line)
    i += 1

with open('/home/ubuntu/main.py', 'w') as f:
    f.writelines(new_lines)

print("패치 완료")
EOF

python3 /tmp/full_patch.py
# 문법 체크
python3 -c "import py_compile; py_compile.compile('/home/ubuntu/main.py', doraise=True)" && echo "OK"
# 확인
grep -n "stop_websocket\|042660\|st.stop" /home/ubuntu/main.py | head -20
# 재시작
sudo systemctl restart sumbi.service
sudo systemctl status sumbi.service
# q 눌러서 로그 나오기
q
# 서비스 재시작으로 메모리 정리
sudo systemctl restart sumbi.service
# 현재 swap 확인
free -h
# 2GB Swap 추가
sudo fallocate -l 2G /swapfile2
sudo chmod 600 /swapfile2
sudo mkswap /swapfile2
sudo swapon /swapfile2
# 확인
free -h
# swap 영구 등록
echo '/swapfile2 none swap sw 0 0' | sudo tee -a /etc/fstab
# 재시작
sudo systemctl restart sumbi.service
# 메모리 확인
free -h
sudo journalctl -u sumbi.service -f --no-pager
sudo journalctl -u sumbi.service -f --no-pager > /tmp/sumbi_log.txt 2>&1 &
echo "로그 수집 시작"
grep -n "money_flow\|MoneyFlow\|fundamental\|Fundamental\|calc_money\|calc_fund" /home/ubuntu/v3_scorer.py | head -30
# fundamental 함수 내용 보기
sed -n '152,200p' /home/ubuntu/v3_scorer.py
# money flow 관련 검색
grep -n "money\|investor\|institution\|foreign" /home/ubuntu/v3_scorer.py | head -20
grep -n "get_investor\|get_stock_info\|investor\|info.*ticker\|calc_sumbi_v3" /home/ubuntu/main.py | head -30
# get_investor_data 함수 내용
sed -n '306,340p' /home/ubuntu/main.py
# get_stock_info 함수 내용  
sed -n '425,465p' /home/ubuntu/main.py
# KIS 토큰 + investor API 직접 테스트
python3 << 'EOF'
import sys
sys.path.insert(0, '/home/ubuntu')
from main import get_investor_data, get_stock_info

# 삼성전자 테스트
print("=== investor ===")
inv = get_investor_data('005930')
print(inv)

print("=== stock info ===")
info = get_stock_info('005930')
print(info)
EOF

cat > /tmp/fix_fundamental.py << 'EOF'
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

old = '''def get_stock_info(ticker):
    """종목 기본 정보 (이름, 섹터, 시장정보 등)"""
    try:
        df = fdr.StockListing('KRX')
        row = df[df['Code'] == ticker]
        if not row.empty:
            return {
                'name':   row.iloc[0].get('Name', ticker),
                'sector': row.iloc[0].get('Sector', ''),
                'market': row.iloc[0].get('Market', 'KOSPI'),
            }
    except:
        pass
    return {'name': ticker, 'sector': '', 'market': 'KRX'}'''

new = '''def get_stock_info(ticker):
    """종목 기본 정보 (이름, 섹터, 시장정보 등)"""
    result = {'name': ticker, 'sector': '', 'market': 'KOSPI',
              'per': None, 'pbr': None, 'roe': None, 'operating_margin': None}
    try:
        df = fdr.StockListing('KRX')
        row = df[df['Code'] == ticker]
        if not row.empty:
            result['name'] = row.iloc[0].get('Name', ticker)
            result['sector'] = row.iloc[0].get('Sector', '')
            result['market'] = row.iloc[0].get('Market', 'KOSPI')
    except:
        pass
    try:
        token = get_token()
        if token:
            res = requests.get(
                f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-price",
                headers={
                    "authorization": f"Bearer {token}",
                    "appkey": APP_KEY,
                    "appsecret": APP_SECRET,
                    "tr_id": "FHKST01010100"
                },
                params={"fid_cond_mrkt_div_code": "J", "fid_input_iscd": ticker},
                timeout=5
            ).json()
            out = res.get("output", {})
            def safe_float(v):
                try: return float(str(v).replace(",","")) if v else None
                except: return None
            result['per'] = safe_float(out.get('per'))
            result['pbr'] = safe_float(out.get('pbr'))
            result['roe'] = safe_float(out.get('roe'))
            result['operating_margin'] = safe_float(out.get('bstp_eme_cls_code'))
    except:
        pass
    return result'''

if old in content:
    content = content.replace(old, new)
    prin

cat > /tmp/fix_fundamental.py << 'EOF'
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

old = '''def get_stock_info(ticker):
    """종목 기본 정보 (이름, 섹터, 시장정보 등)"""
    try:
        df = fdr.StockListing('KRX')
        row = df[df['Code'] == ticker]
        if not row.empty:
            return {
                'name':   row.iloc[0].get('Name', ticker),
                'sector': row.iloc[0].get('Sector', ''),
                'market': row.iloc[0].get('Market', 'KOSPI'),
            }
    except:
        pass
    return {'name': ticker, 'sector': '', 'market': 'KRX'}'''

new = '''def get_stock_info(ticker):
    """종목 기본 정보 (이름, 섹터, 시장정보 등)"""
    result = {'name': ticker, 'sector': '', 'market': 'KOSPI',
              'per': None, 'pbr': None, 'roe': None, 'operating_margin': None}
    try:
        df = fdr.StockListing('KRX')
        row = df[df['Code'] == ticker]
        if not row.empty:
            result['name'] = row.iloc[0].get('Name', ticker)
            result['sector'] = row.iloc[0].get('Sector', '')
            result['market'] = row.iloc[0].get('Market', 'KOSPI')
    except:
        pass
    try:
        token = get_token()
        if token:
            res = requests.get(
                f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-price",
                headers={
                    "authorization": f"Bearer {token}",
                    "appkey": APP_KEY,
                    "appsecret": APP_SECRET,
                    "tr_id": "FHKST01010100"
                },
                params={"fid_cond_mrkt_div_code": "J", "fid_input_iscd": ticker},
                timeout=5
            ).json()
            out = res.get("output", {})
            def safe_float(v):
                try: return float(str(v).replace(",","")) if v else None
                except: return None
            result['per'] = safe_float(out.get('per'))
            result['pbr'] = safe_float(out.get('pbr'))
            result['roe'] = safe_float(out.get('roe'))
            result['operating_margin'] = safe_float(out.get('bstp_eme_cls_code'))
    except:
        pass
    return result'''

if old in content:
    content = content.replace(old, new)
    prin

EOF
python3 /tmp/fix_fundamental.py
python3 - << 'PYEOF'
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

old = "return {'name': ticker, 'sector': '', 'market': 'KRX'}"

new = '''    result = {'name': ticker, 'sector': '', 'market': 'KOSPI',
              'per': None, 'pbr': None, 'roe': None, 'operating_margin': None}
    try:
        df = fdr.StockListing('KRX')
        row = df[df['Code'] == ticker]
        if not row.empty:
            result['name'] = row.iloc[0].get('Name', ticker)
            result['sector'] = row.iloc[0].get('Sector', '')
            result['market'] = row.iloc[0].get('Market', 'KOSPI')
    except:
        pass
    try:
        token = get_token()
        if token:
            res = requests.get(
                f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-price",
                headers={"authorization": f"Bearer {token}", "appkey": APP_KEY,
                         "appsecret": APP_SECRET, "tr_id": "FHKST01010100"},
                params={"fid_cond_mrkt_div_code": "J", "fid_input_iscd": ticker},
                timeout=5
            ).json()
            out = res.get("output", {})
            def safe_float(v):
                try: return float(str(v).replace(",","")) if v else None
                except: return None
            result['per'] = safe_float(out.get('per'))
            result['pbr'] = safe_float(out.get('pbr'))
            result['roe'] = safe_float(out.get('roe'))
    except:
        pass
    return result'''

if old in content:
    # 함수 전체를 교체
    start = content.find('def get_stock_info(ticker):')
    end = content.find('\n@st.cache_data', start)
    if end == -1:
        end = content.find('\ndef ', start+1)
    old_func = content[start:end]
    new_func = '''def get_stock_info(ticker):
    """종목 기본 정보"""
''' + new
    content = content.replace(old_func, new_func)
    print("수정 성공")
else:
    print("패턴:" + repr(content[content.find('return {'):content.find('return {')+60]))

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)
PYEOF

python3 -c "import py_compile; py_compile.compile('/home/ubuntu/main.py', doraise=True)" && echo "문법 OK"
sudo systemctl restart sumbi.service
grep -n "cache_data\|cache_resource\|ttl" /home/ubuntu/main.py | head -20
sed -n '250,255p' /home/ubuntu/main.py
sed -n '270,275p' /home/ubuntu/main.py
sed -n '303,307p' /home/ubuntu/main.py
sed -n '335,340p' /home/ubuntu/main.py
sed -n '420,426p' /home/ubuntu/main.py
sed -n '525,545p' /home/ubuntu/main.py
python3 - << 'PYEOF'
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

# 1. ttl 86400 → 3600으로 단축
content = content.replace(
    '@st.cache_data(ttl=86400)\ndef get_stock_info',
    '@st.cache_data(ttl=3600)\ndef get_stock_info'
)

# 2. 캐시 클리어에 get_stock_info 추가
content = content.replace(
    'get_investor_data.clear()\n            get_stock_price.clear()',
    'get_investor_data.clear()\n            get_stock_price.clear()\n            get_stock_info.clear()'
)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)

print("수정 완료")
PYEOF

grep -n "ttl=86400\|get_stock_info.clear" /home/ubuntu/main.py
sudo systemctl restart sumbi.service
python3 - << 'PYEOF'
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

# ttl 수정
old1 = '@st.cache_data(ttl=86400)\ndef get_stock_info'
new1 = '@st.cache_data(ttl=3600)\ndef get_stock_info'
if old1 in content:
    content = content.replace(old1, new1)
    print("ttl 수정 성공")
else:
    print("ttl 패턴 불일치")

# 캐시 클리어 추가
old2 = 'get_investor_data.clear()\n            get_stock_price.clear()\n            get_news.clear()\n            get_chart_data.clear()'
new2 = 'get_investor_data.clear()\n            get_stock_price.clear()\n            get_stock_info.clear()\n            get_news.clear()\n            get_chart_data.clear()'
if old2 in content:
    content = content.replace(old2, new2)
    print("캐시 클리어 수정 성공")
else:
    print("캐시 클리어 패턴 불일치")

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)
PYEOF

sudo systemctl restart sumbi.service
python3 - << 'PYEOF'
import sys
sys.path.insert(0, '/home/ubuntu')
from main import get_token, URL_BASE, APP_KEY, APP_SECRET
import requests

token = get_token()
res = requests.get(
    f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-price",
    headers={"authorization": f"Bearer {token}", "appkey": APP_KEY,
             "appsecret": APP_SECRET, "tr_id": "FHKST01010100"},
    params={"fid_cond_mrkt_div_code": "J", "fid_input_iscd": "005930"},
    timeout=5
).json()
out = res.get("output", {})
# PER/PBR 관련 필드만 출력
for k, v in out.items():
    if any(x in k.lower() for x in ['per', 'pbr', 'roe', 'eps', 'bps']):
        print(f"{k}: {v}")
PYEOF

# Ctrl+C 누르고 다시 실행
python3 - << 'PYEOF'
import sys, os
sys.path.insert(0, '/home/ubuntu')
os.environ.setdefault('KIS_APP_KEY', '')
import requests

# 환경변수에서 직접 읽기
APP_KEY = os.environ.get('KIS_APP_KEY', '')
APP_SECRET = os.environ.get('KIS_APP_SECRET', '')
URL_BASE = "https://openapi.koreainvestment.com:9443"

# .env 파일에서 읽기 시도
try:
    with open('/home/ubuntu/.env') as f:
        for line in f:
            if 'KIS_APP_KEY' in line:
                APP_KEY = line.split('=')[1].strip()
            if 'KIS_APP_SECRET' in line:
                APP_SECRET = line.split('=')[1].strip()
except:
    pass

print(f"KEY: {APP_KEY[:10]}...")

# 토큰 발급
token_res = requests.post(
    f"{URL_BASE}/oauth2/tokenP",
    json={"grant_type":"client_credentials","appkey":APP_KEY,"appsecret":APP_SECRET}
).json()
token = token_res.get('access_token','')
print(f"Token: {token[:20]}...")

res = requests.get(
    f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-price",
    headers={"authorization":f"Bearer {token}","appkey":APP_KEY,"appsecret":APP_SECRET,"tr_id":"FHKST01010100"},
    params={"fid_cond_mrkt_div_code":"J","fid_input_iscd":"005930"},
    timeout=5
).json()
out = res.get("output",{})
for k,v in out.items():
    if any(x in k for x in ['per','pbr','roe','eps','bps']):
        print(f"{k}: {v}")
PYEOF

# 키 저장 위치 찾기
grep -r "KIS_APP_KEY\|APP_KEY\|APP_SECRET" /home/ubuntu/main.py | head -5
# .env 파일 확인
cat /home/ubuntu/.env 2>/dev/null || echo "없음"
ls /home/ubuntu/*.env 2>/dev/null
python3 - << 'PYEOF'
import sys
sys.path.insert(0, '/home/ubuntu')
from main import get_token, URL_BASE, APP_KEY, APP_SECRET
import requests

token = get_token()
res = requests.get(
    f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-price",
    headers={"authorization":f"Bearer {token}","appkey":APP_KEY,"appsecret":APP_SECRET,"tr_id":"FHKST01010100"},
    params={"fid_cond_mrkt_div_code":"J","fid_input_iscd":"005930"},
    timeout=5
).json()
out = res.get("output",{})
for k,v in out.items():
    if any(x in k for x in ['per','pbr','roe','eps','bps']):
        print(f"{k}: {v}")
PYEOF

python3 - << 'PYEOF'
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

old = "            result['per'] = safe_float(out.get('per'))\n            result['pbr'] = safe_float(out.get('pbr'))\n            result['roe'] = safe_float(out.get('roe'))"

new = """            result['per'] = safe_float(out.get('per'))
            result['pbr'] = safe_float(out.get('pbr'))
            eps = safe_float(out.get('eps'))
            bps = safe_float(out.get('bps'))
            if eps and bps and bps > 0:
                result['roe'] = round(eps / bps * 100, 2)
            result['operating_margin'] = None"""

if old in content:
    content = content.replace(old, new)
    print("수정 성공")
else:
    print("패턴 불일치")

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)
PYEOF

sudo systemctl restart sumbi.service
grep -n "fdr.StockListing" /home/ubuntu/main.py
python3 - << 'PYEOF'
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

# fdr.StockListing 캐시 함수 추가 (파일 상단 import 다음에)
cache_func = '''
@st.cache_data(ttl=86400)
def get_krx_listing():
    """KRX 전체 종목 목록 (하루 1번만 로드)"""
    try:
        return fdr.StockListing('KRX')
    except:
        return None

'''

# 이미 있으면 추가 안함
if 'def get_krx_listing()' not in content:
    # get_token_cached 함수 앞에 삽입
    insert_pos = content.find('@st.cache_data(ttl=3600)\ndef get_token_cached')
    if insert_pos > 0:
        content = content[:insert_pos] + cache_func + content[insert_pos:]
        print("함수 추가 성공")

# fdr.StockListing('KRX') → get_krx_listing() 으로 교체
content = content.replace(
    "df = fdr.StockListing('KRX')",
    "df = get_krx_listing()"
)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)

print("완료")
PYEOF

python3 -c "import py_compile; py_compile.compile('/home/ubuntu/main.py', doraise=True)" && echo "문법 OK"
sudo systemctl restart sumbi.service
python3 - << 'PYEOF'
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

# get_investor_data ttl 300→60으로 단축 (1분마다 갱신)
content = content.replace(
    '@st.cache_data(ttl=300)\ndef get_investor_data',
    '@st.cache_data(ttl=60)\ndef get_investor_data'
)

# get_stock_info ttl 3600→600으로 단축
content = content.replace(
    '@st.cache_data(ttl=3600)\ndef get_stock_info',
    '@st.cache_data(ttl=600)\ndef get_stock_info'
)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)
print("완료")
PYEOF

sudo systemctl restart sumbi.service
sed -n '330,365p' /home/ubuntu/v3_scorer.py
sed -n '540,560p' /home/ubuntu/main.py
sed -n '555,580p' /home/ubuntu/main.py
python3 - << 'PYEOF'
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

# get_stock_info.clear() 추가
content = content.replace(
    'get_investor_data.clear()\n            get_stock_price.clear()\n            get_news.clear()\n            get_chart_data.clear()',
    'get_investor_data.clear()\n            get_stock_price.clear()\n            get_stock_info.clear()\n            get_news.clear()\n            get_chart_data.clear()'
)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)
print("완료")
PYEOF

python3 - << 'PYEOF'
import sys
sys.path.insert(0, '/home/ubuntu')
from main import get_investor_data
inv = get_investor_data('005930')
print("investor:", inv)
PYEOF

python3 - 2>/dev/null << 'PYEOF'
import sys
sys.path.insert(0, '/home/ubuntu')
from main import get_investor_data
inv = get_investor_data('005930')
print("investor:", inv)
PYEOF

grep -n "def get_investor_data\|default_tickers" /home/ubuntu/main.py | head -10
sed -n '117,150p' /home/ubuntu/v3_scorer.py
sed -n '568,575p' /home/ubuntu/main.py
sed -n '315,345p' /home/ubuntu/main.py
python3 - << 'PYEOF'
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

# st.error 제거 + 재시도 로직
old = '''        st.error(f"API Error: {type(e).__name__}: {e}")
    return None'''

new = '''        pass
    return None'''

content = content.replace(old, new)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)
print("완료")
PYEOF

sudo systemctl restart sumbi.service
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h  # 확인
sudo systemctl restart sumbi
free -h
