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
def probe(label, path, tr, params):
    print("\n===== %s | tr=%s =====" % (label, tr))
    try:
        r = requests.get(BASE+path,
            headers={"authorization":"Bearer "+str(tok),"appkey":AK,"appsecret":AS,"tr_id":tr},
            params=params, timeout=10)
        print("HTTP:", r.status_code)
        j = r.json()
        print("rt_cd:", j.get("rt_cd"), "| msg:", j.get("msg1"))
        out = j.get("output") or j.get("output1") or j.get("output2")
        if isinstance(out, list) and out:
            print("ROWS:", len(out))
            print("FIELDS:", list(out[0].keys()))
            print(json.dumps(out[0], ensure_ascii=False)[:900])
        elif isinstance(out, dict):
            print("FIELDS:", list(out.keys()))
            print(json.dumps(out, ensure_ascii=False)[:900])
        else:
            print("RAW:", json.dumps(j, ensure_ascii=False)[:900])
    except Exception as e:
        print("EXC:", type(e).__name__, e)
# 후보 A: 공매도잔고 일별 (FHPST04830000 변형 - 잔고 엔드포인트)
probe("A short-sale-daily-trend balance", "/uapi/domestic-stock/v1/quotations/daily-short-sale", "FHPST04830000",
      {"fid_cond_mrkt_div_code":"J","fid_input_iscd":"005930","fid_input_date_1":d1,"fid_input_date_2":today,"fid_period_div_code":"D"})
# 후보 B: 공매도 잔고 (FHPST04010000)
probe("B short-balance FHPST04010000", "/uapi/domestic-stock/v1/quotations/daily-loan-trans", "FHPST04010000",
      {"fid_cond_mrkt_div_code":"J","fid_input_iscd":"005930","fid_input_date_1":d1,"fid_input_date_2":today,"fid_period_div_code":"D"})
