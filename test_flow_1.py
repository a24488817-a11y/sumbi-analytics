import requests, json

URL = 'http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd'
HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'http://data.krx.co.kr/',
}

def fetch(isin, strt, end):
    data = {
        'bld': 'dbms/MDC/STAT/standard/MDCSTAT02302',
        'strtDd': strt,
        'endDd': end,
        'isuCd': isin,
        'inqTpCd': '2',
        'trdVolVal': '2',
        'askBid': '3',
    }
    r = requests.post(URL, data=data, headers=HEADERS, timeout=15)
    return r.json()

ISIN = 'KR7005930003'  # Samsung
print("=== TEST 1: recent 1 month (column check) ===")
j = fetch(ISIN, '20260501', '20260603')
out = j.get('output', [])
print("rows:", len(out))
if out:
    print("FIRST ROW KEYS:", list(out[0].keys()))
    print("FIRST ROW:", json.dumps(out[0], ensure_ascii=False))
    print("LAST ROW:", json.dumps(out[-1], ensure_ascii=False))

print()
print("=== TEST 2: full 10yr (row count check) ===")
j2 = fetch(ISIN, '20150101', '20260603')
out2 = j2.get('output', [])
print("rows:", len(out2))
if out2:
    dates = [r.get('TRD_DD') for r in out2 if r.get('TRD_DD')]
    print("first:", min(dates), "last:", max(dates))
