import os, requests

krx_id, krx_pw = "", ""
with open(os.path.expanduser("~/.env"), "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line.startswith("KRX_ID="): krx_id = line.split("=", 1)[1].strip(' "\'')
        if line.startswith("KRX_PW="): krx_pw = line.split("=", 1)[1].strip(' "\'')

print(f"[DEBUG] ID: {krx_id}")
print(f"[DEBUG] PW Length: {len(krx_pw)}")

s = requests.Session()
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
p1 = "https://data.krx.co.kr/contents/MDC/COMS/client/MDCCOMS001.cmd"
p2 = "https://data.krx.co.kr/contents/MDC/COMS/client/view/login.jsp?site=mdc"
p3 = "https://data.krx.co.kr/contents/MDC/COMS/client/MDCCOMS001D1.cmd"

s.get(p1, headers={"User-Agent": ua}, timeout=15)
s.get(p2, headers={"User-Agent": ua, "Referer": p1}, timeout=15)

payload = {"mbrNm": "", "telNo": "", "di": "", "certType": "", "mbrId": krx_id, "pw": krx_pw}
headers = {"User-Agent": ua, "Referer": p1}
res = s.post(p3, data=payload, headers=headers, timeout=15)

print("\n--- LOGIN RESULT ---")
try:
    js = res.json()
    print("CODE:", js.get("_error_code"), "/ MSG:", js.get("_error_msg", "OK"))
    if js.get("_error_code") == "CD011":
        payload["skipDup"] = "Y"
        res = s.post(p3, data=payload, headers=headers, timeout=15)
        print("DUP FIXED:", res.json().get("_error_code"))
except Exception as e:
    print("ERR:", res.text[:50])

print("\n--- FETCHING DATA ---")
url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
headers["Referer"] = "https://data.krx.co.kr/contents/MDC/MDI/outerLoader/index.cmd"

# 정답 후보 2개를 한 번에 모두 테스트
for bld in ["MDCSTAT02402", "MDCSTAT02303"]:
    print(f"\n[TRY] {bld}")
    d = {
        "bld": f"dbms/MDC/STAT/standard/{bld}",
        "isuCd": "KR7005930003",
        "isuCd2": "KR7005930003",
        "strtDd": "20240101",
        "endDd": "20240110",
        "inqTpCd": "2",
        "trdVolVal": "2",
        "askBid": "3",
        "share": "1",
        "money": "1",
        "csvxls_isNo": "false"
    }
    r = s.post(url, data=d, headers=headers, timeout=15)
    print("STATUS:", r.status_code)
    if r.status_code == 200 and "LOGOUT" not in r.text:
        try:
            out = r.json().get("output", [])
            print(f"SUCCESS! Rows: {len(out)}")
            if out: print("KEYS:", list(out[0].keys()))
        except:
            print("JSON ERR")
    else:
        print("FAIL (LOGOUT)")
