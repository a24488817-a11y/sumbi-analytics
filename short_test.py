#!/usr/bin/env python3
import os, json, requests
from datetime import datetime, timedelta
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.expanduser("~/.env")); load_dotenv()
except Exception:
    pass
AK = os.environ.get("KIS_APP_KEY")
AS = os.environ.get("KIS_APP_SECRET")
BASE = "https://openapi.koreainvestment.com:9443"
tok = requests.post(BASE+"/oauth2/tokenP",
    json={"grant_type":"client_credentials","appkey":AK,"appsecret":AS},
    timeout=10).json().get("access_token")
print("TOKEN:", "OK" if tok else "FAIL")
today = datetime.now().strftime("%Y%m%d")
d1 = (datetime.now()-timedelta(days=30)).strftime("%Y%m%d")
r = requests.get(BASE+"/uapi/domestic-stock/v1/quotations/daily-short-sale",
    headers={"authorization":"Bearer "+str(tok),"appkey":AK,"appsecret":AS,"tr_id":"FHPST04830000"},
    params={"fid_cond_mrkt_div_code":"J","fid_input_iscd":"005930",
            "fid_input_date_1":d1,"fid_input_date_2":today,"fid_period_div_code":"D"},
    timeout=10)
print("HTTP:", r.status_code)
j = r.json()
print("rt_cd:", j.get("rt_cd"), "| msg:", j.get("msg1"))
out = j.get("output") or j.get("output1") or j.get("output2")
print("OUTPUT_TYPE:", type(out).__name__)
if isinstance(out, list):
    print("ROWS:", len(out))
    if out:
        print("FIELDS:", list(out[0].keys()))
        print(json.dumps(out[0], ensure_ascii=False, indent=2))
else:
    print(json.dumps(j, ensure_ascii=False, indent=2)[:1500])
