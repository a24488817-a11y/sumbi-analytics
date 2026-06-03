import requests, json

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest',
    'Origin': 'http://data.krx.co.kr',
    'Referer': 'http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020203',
})

s.get('http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020203', timeout=15)

URL = 'http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd'
data = {
    'bld': 'dbms/MDC/STAT/standard/MDCSTAT02302',
    'locale': 'ko_KR',
    'isuCd': 'KR7005930003',
    'strtDd': '20260501',
    'endDd': '20260603',
    'share': '1',
    'money': '1',
    'csvxls_isNo': 'false',
}
r = s.post(URL, data=data, timeout=15)
print("STATUS", r.status_code, "CT", r.headers.get('content-type'))
print("BODY_HEAD")
print(r.text[:500])
