import os, requests

krx_id, krx_pw = "", ""
# 1. Credentials 로드 (따옴표 안전 제거)
with open(os.path.expanduser("~/.env"), "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line.startswith("KRX_ID="): krx_id = line.split("=", 1)[1].strip(' "\'')
        if line.startswith("KRX_PW="): krx_pw = line.split("=", 1)[1].strip(' "\'')

if not krx_id or not krx_pw:
    print("ERROR: ~/.env 파일에 KRX_ID 또는 KRX_PW 값이 비어있습니다.")
    exit(1)

s = requests.Session()
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# 2. 2026년 최신 KRX 로그인 플로우
p1 = "https://data.krx.co.kr/contents/MDC/COMS/client/MDCCOMS001.cmd"
p2 = "https://data.krx.co.kr/contents/MDC/COMS/client/view/login.jsp?site=mdc"
p3 = "https://data.krx.co.kr/contents/MDC/COMS/client/MDCCOMS001D1.cmd"

s.get(p1, headers={"User-Agent": ua}, timeout=15)
s.get(p2, headers={"User-Agent": ua, "Referer": p1}, timeout=15)

payload = {"mbrNm": "", "telNo": "", "di": "", "certType": "", "mbrId": krx_id, "pw": krx_pw}
headers = {"User-Agent": ua, "Referer": p1}
res = s.post(p3, data=payload, headers=headers, timeout=15)

try:
    if res.json().get("_error_code") == "CD011":
        payload["skipDup"] = "Y"
        s.post(p3, data=payload, headers=headers, timeout=15)
except: pass

print("[INFO] Login Attempt Finished. Fetching Data...")

# 3. MDCSTAT02303 데이터 호출 (투자자별 개별종목 일별)
url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
headers["Referer"] = "https://data.krx.co.kr/contents/MDC/MDI/outerLoader/index.cmd"

d = {
    "bld": "dbms/MDC/STAT/standard/MDCSTAT02303",
    "isuCd": "KR7005930003",
    "strtDd": "20150101",
    "endDd": "20150110",
    "inqTpCd": "2",
    "trdVolVal": "2",
    "askBid": "3",
    "share": "1",
    "money": "1",
    "csvxls_isNo": "false"
}

r = s.post(url, data=d, headers=headers, timeout=15)
print("[STATUS]", r.status_code)

try:
    js = r.json()
    if "output" in js and len(js["output"]) > 0:
        print("[SUCCESS] Rows:", len(js["output"]))
        for k, v in js["output"][0].items():
            print(f"  {k}: {v}")
    else:
        print("[FAIL - NO DATA]", r.text[:300])
except Exception as e:
    print("[JSON ERROR]", e)
    print("[RAW]", r.text[:300])
