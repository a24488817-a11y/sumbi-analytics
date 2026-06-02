import requests
import json
import pprint

app_key, app_secret = "", ""

# 1. main.py에서 정확히 변수 선언문만 정밀 타격 (줄 시작이 APP_KEY / APP_SECRET인 것)
with open("main.py", "r", encoding="utf-8") as f:
    for line in f:
        stripped = line.strip()
        if stripped.startswith("APP_KEY") and "=" in stripped:
            parts = stripped.split("=", 1)
            app_key = parts[1].strip().strip('"').strip("'")
        if stripped.startswith("APP_SECRET") and "=" in stripped:
            parts = stripped.split("=", 1)
            app_secret = parts[1].strip().strip('"').strip("'")

print(f"🔑 [정밀 인양 검증] APP_KEY 수집 완료 | 토큰 가동 시도...")

if not app_key or not app_secret:
    print("❌ 에러: main.py에서 APP_KEY 또는 APP_SECRET 변수를 찾지 못했습니다.")
    exit()

# 2. 독립 전술 토큰 발급
url_token = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
res_token = requests.post(url_token, headers={"content-type": "application/json"}, data=json.dumps({
    "grant_type": "client_credentials", "appkey": app_key, "appsecret": app_secret
}))
token_json = res_token.json()
token = token_json.get("access_token")

if not token:
    print("❌ 토큰 발급 실패. 증권사 응답:")
    pprint.pprint(token_json)
    exit()

print("🚀 정품 토큰 승인 완료! KIS 서버 본진 비밀 Key 인양 작전 전개...")

# 3. KIS 서버 본진 원본 데이터 전량 인양
url_data = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/inquire-investor"
res_data = requests.get(url_data, headers={
    "Content-Type": "application/json", "authorization": f"Bearer {token}",
    "appkey": app_key, "appsecret": app_secret, "tr_id": "FHKST01010900"
}, params={"fid_cond_mrkt_div_code": "J", "fid_input_iscd": "042660"})

res_json = res_data.json()
output = res_json.get("output", [])

if output and len(output) > 0:
    print("\n======= 🎯 [한국투자증권 정품 KEY 목록 인양 성공!] =======")
    for k in output[0].keys():
        print(f"- {k}")
    print("========================================================\n")
else:
    print("\n======= ⚠️ [서버 응답 성공 / 주말 데이터 구조 검증] =======")
    pprint.pprint(res_json)
    print("========================================================\n")
