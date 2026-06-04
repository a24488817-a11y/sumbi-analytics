import os, requests, time, csv, datetime, sys

def get_stocks():
    s = requests.Session()
    d = {"bld": "dbms/comm/finder/finder_stkisu", "mktsel": "ALL", "typeNo": "0", "searchText": ""}
    return s.post("http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd", data=d, timeout=15).json().get("block1", [])

def run_flow():
    os.makedirs(os.path.expanduser("~/data/flow"), exist_ok=True)
    krx_id, krx_pw = "", ""
    with open(os.path.expanduser("~/.env"), "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("KRX_ID="): krx_id = line.strip().split("=", 1)[1].strip(' "\'')
            if line.startswith("KRX_PW="): krx_pw = line.strip().split("=", 1)[1].strip(' "\'')

    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0"})
    p1 = "https://data.krx.co.kr/contents/MDC/COMS/client/MDCCOMS001.cmd"
    s.get(p1, timeout=15)
    s.get("https://data.krx.co.kr/contents/MDC/COMS/client/view/login.jsp?site=mdc", headers={"Referer": p1}, timeout=15)

    payload = {"mbrNm": "", "telNo": "", "di": "", "certType": "", "mbrId": krx_id, "pw": krx_pw}
    res = s.post("https://data.krx.co.kr/contents/MDC/COMS/client/MDCCOMS001D1.cmd", data=payload, headers={"Referer": p1}, timeout=15)
    if res.json().get("_error_code") == "CD011":
        payload["skipDup"] = "Y"
        s.post("https://data.krx.co.kr/contents/MDC/COMS/client/MDCCOMS001D1.cmd", data=payload, headers={"Referer": p1}, timeout=15)

    stocks = get_stocks()
    print(f"[FLOW] Start {len(stocks)} stocks...")
    today = datetime.date.today()

    for i, stock in enumerate(stocks):
        code, full = stock["short_code"], stock["full_code"]
        csv_path = os.path.expanduser(f"~/data/flow/{code}.csv")
        if os.path.exists(csv_path): continue

        all_rows = []
        for year in range(2015, today.year + 1):
            d = {
                "bld": "dbms/MDC/STAT/standard/MDCSTAT02402",
                "isuCd": full, "isuCd2": full,
                "strtDd": f"{year}0101", "endDd": f"{year}1231" if year < today.year else today.strftime("%Y%m%d"),
                "inqTpCd": "2", "trdVolVal": "2", "askBid": "3", "share": "1", "money": "1", "csvxls_isNo": "false"
            }
            for _ in range(3):
                try:
                    r = s.post("http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd", data=d, timeout=15)
                    out = r.json().get("output")
                    if out is not None:
                        all_rows.extend(out)
                        break
                except: time.sleep(5)
            time.sleep(1)

        if all_rows:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
                w.writeheader()
                w.writerows(all_rows)
        if (i + 1) % 50 == 0: print(f"[FLOW] {i + 1} / {len(stocks)}")
    print("[FLOW] DONE!")

def run_price():
    os.makedirs(os.path.expanduser("~/data/price"), exist_ok=True)
    env = {}
    with open(os.path.expanduser("~/.env"), "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                env[k] = v.strip(' "\'')

    url_base, ak, ask = env.get("URL_BASE", "https://openapi.koreainvestment.com:9443"), env["KIS_APP_KEY"], env["KIS_APP_SECRET"]
    r_tok = requests.post(f"{url_base}/oauth2/tokenP", json={"grant_type":"client_credentials", "appkey":ak, "appsecret":ask}).json()
    token = r_tok.get("access_token")

    stocks = get_stocks()
    print(f"[PRICE] Start {len(stocks)} stocks...")
    headers = {"authorization": f"Bearer {token}", "appkey": ak, "appsecret": ask, "tr_id": "FHKST03010100", "custtype": "P"}

    for i, stock in enumerate(stocks):
        code = stock["short_code"]
        csv_path = os.path.expanduser(f"~/data/price/{code}.csv")
        if os.path.exists(csv_path): continue

        all_rows = []
        d2 = datetime.date.today()
        while d2 >= datetime.date(2015, 1, 1):
            d1 = max(d2 - datetime.timedelta(days=140), datetime.date(2015, 1, 1))
            params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_INPUT_DATE_1": d1.strftime("%Y%m%d"), "FID_INPUT_DATE_2": d2.strftime("%Y%m%d"), "FID_PERIOD_DIV_CODE": "D", "FID_ORG_ADJ_PRC": "0"}
            
            js = {}
            for _ in range(3):
                try:
                    js = requests.get(f"{url_base}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice", headers=headers, params=params, timeout=15).json()
                    break
                except: time.sleep(5)
                    
            out2 = js.get("output2", [])
            if not out2 or not out2[0].get("stck_bsop_date"): break
            
            valid = [r for r in out2 if r.get("stck_bsop_date")]
            all_rows.extend(valid)
            d2 = datetime.datetime.strptime(valid[-1]["stck_bsop_date"], "%Y%m%d").date() - datetime.timedelta(days=1)
            time.sleep(0.3)

        if all_rows:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["stck_bsop_date", "stck_clpr", "stck_oprc", "stck_hgpr", "stck_lwpr", "acml_vol"], extrasaction="ignore")
                w.writeheader()
                w.writerows(all_rows)
        if (i + 1) % 50 == 0: print(f"[PRICE] {i + 1} / {len(stocks)}")
    print("[PRICE] DONE!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "price": run_price()
    else: run_flow()
