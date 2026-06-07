from main import get_token, URL_BASE, APP_KEY, APP_SECRET
import requests, json
tok = get_token()
url = URL_BASE + "/uapi/domestic-stock/v1/quotations/daily-short-sale"
h = {"authorization":"Bearer "+tok,"appkey":APP_KEY,"appsecret":APP_SECRET,"tr_id":"FHPST04830000","custtype":"P"}
p = {"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":"005930","FID_INPUT_DATE_1":"20260601","FID_INPUT_DATE_2":"20260605"}
r = requests.get(url, headers=h, params=p, timeout=10)
print("HTTP", r.status_code)
print(json.dumps(r.json(), ensure_ascii=False, indent=1)[:1500])
