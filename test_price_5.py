import os, time, requests
from datetime import datetime, timedelta

def load_env(path):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env

ENV = load_env(os.path.expanduser('~/.env'))
APP_KEY = ENV['KIS_APP_KEY']
APP_SECRET = ENV['KIS_APP_SECRET']
BASE = ENV.get('URL_BASE', 'https://openapi.koreainvestment.com:9443').rstrip('/')

def get_token():
    url = BASE + '/oauth2/tokenP'
    body = {"grant_type": "client_credentials", "appkey": APP_KEY, "appsecret": APP_SECRET}
    r = requests.post(url, json=body, timeout=10)
    r.raise_for_status()
    return r.json()['access_token']

TOKEN = get_token()
print("TOKEN_OK")

def fetch_chunk(code, d1, d2):
    url = BASE + '/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice'
    headers = {
        "authorization": "Bearer " + TOKEN,
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "FHKST03010100",
        "custtype": "P",
    }
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code,
        "FID_INPUT_DATE_1": d1,
        "FID_INPUT_DATE_2": d2,
        "FID_PERIOD_DIV_CODE": "D",
        "FID_ORG_ADJ_PRC": "0",
    }
    for attempt in range(3):
        try:
            r = requests.get(url, headers=headers, params=params, timeout=10)
            j = r.json()
            if j.get('rt_cd') == '0':
                return j.get('output2', []) or []
            print("  WARN", code, j.get('msg_cd'), j.get('msg1'))
            return []
        except Exception as e:
            print("  retry", code, e)
            time.sleep(30)
    return []

def fetch_all(code, start='20150101'):
    rows = {}
    end = datetime.today()
    prev_oldest = None
    while True:
        d2 = end.strftime('%Y%m%d')
        d1 = (end - timedelta(days=140)).strftime('%Y%m%d')
        if d1 < start:
            d1 = start
        chunk = fetch_chunk(code, d1, d2)
        time.sleep(0.3)
        if not chunk:
            break
        for row in chunk:
            d = row.get('stck_bsop_date')
            if d and d >= start:
                rows[d] = row
        dates = [r['stck_bsop_date'] for r in chunk if r.get('stck_bsop_date')]
        if not dates:
            break
        oldest = min(dates)
        if oldest <= start or oldest == prev_oldest:
            break
        prev_oldest = oldest
        end = datetime.strptime(oldest, '%Y%m%d') - timedelta(days=1)
    return rows

TEST = ['005930', '042660', '000660', '035720', '005380']
for code in TEST:
    rows = fetch_all(code)
    if rows:
        ds = sorted(rows.keys())
        print(code, "rows=%d first=%s last=%s" % (len(rows), ds[0], ds[-1]))
    else:
        print(code, "NO_DATA")
