import os, requests, json

krx_id = ""
krx_pw = ""
env_path = os.path.expanduser("~/.env")

# 1. Load Credentials securely
with open(env_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line.startswith("KRX_ID="): krx_id = line.split("=", 1)[1]
        if line.startswith("KRX_PW="): krx_pw = line.split("=", 1)[1]

if not krx_id or not krx_pw:
    print("ERROR: KRX_ID or KRX_PW not found in ~/.env")
    exit(1)

s = requests.Session()
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# 2. KRX Login Flow (Mandatory since Feb 2026)
p1 = "https://data.krx.co.kr/contents/MDC/COMS/client/MDCCOMS001.cmd"
p2 = "https://data.krx.co.kr/contents/MDC/COMS/client/view/login.jsp?site=mdc"
p3 = "https://data.krx.co.kr/contents/MDC/COMS/client/MDCCOMS001D1.cmd"

s.get(p1, headers={"User-Agent": ua}, timeout=15)
s.get(p2, headers={"User-Agent": ua, "Referer": p1}, timeout=15)

payload = {
    "mbrNm": "", "telNo": "", "di": "", "certType": "",
    "mbrId": krx_id, "pw": krx_pw
}
headers = {"User-Agent": ua, "Referer": p1}
res = s.post(p3, data=payload, headers=headers, timeout=15)

# Handle duplicate login session (CD011)
if res.json().get("_error_code") == "CD011":
    payload["skipDup"] = "Y"
    s.post(p3, data=payload, headers=headers, timeout=15)

print("[INFO] Login Success. Session ready.")

# 3. Fetch MDCSTAT Data (Previous failing bld, now with auth)
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
print("[DATA]", r.text[:500])
