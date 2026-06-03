import requests

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020203"
})

# 1. Session Warm-up (정상 접근을 위한 쿠키 발급)
s.get("http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020203", timeout=15)

# 2. 정답 bld 번호(02402)로 데이터 요청 (삼성전자 10일치 테스트)
url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
d = {
    "bld": "dbms/MDC/STAT/standard/MDCSTAT02402",
    "isuCd": "KR7005930003",
    "isuCd2": "KR7005930003",
    "strtDd": "20240101",
    "endDd": "20240110",
    "share": "1",
    "money": "1",
    "csvxls_isNo": "false"
}

r = s.post(url, data=d, timeout=15)
print("[STATUS]", r.status_code)

try:
    js = r.json()
    if "output" in js and len(js["output"]) > 0:
        print("[SUCCESS] Data Rows:", len(js["output"]))
        print("[PREVIEW FIRST ROW]")
        # 투자자 매핑을 위해 첫 줄의 모든 키-값 출력
        for k, v in js["output"][0].items():
            print(f"  {k}: {v}")
    else:
        print("[DATA_NO_OUTPUT]", r.text[:300])
except Exception as e:
    print("[JSON ERROR]", e)
    print("[RAW]", r.text[:300])
