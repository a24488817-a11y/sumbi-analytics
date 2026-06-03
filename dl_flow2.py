import requests, os, time, csv
from datetime import datetime

OUT = os.path.expanduser("~/data/kosdaq_flow")
os.makedirs(OUT, exist_ok=True)
START = "20150101"
END = "20260602"

URL = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
HDR = {"User-Agent": "Mozilla/5.0", "Referer": "http://data.krx.co.kr/"}

def log(m):
    print("[%s] %s" % (datetime.now().strftime("%H:%M:%S"), m), flush=True)

log("Fetching KOSDAQ list...")
r = requests.post(URL, headers=HDR, data={
    "bld": "dbms/comm/finder/finder_stkisu",
    "mktsel": "KSQ",
    "typeNo": "0",
}, timeout=30)
items = r.json()["block1"]
log("Total %d tickers" % len(items))

ok = 0; skip = 0; fail = 0
for i, it in enumerate(items, 1):
    isin = it["full_code"]
    short = it["short_code"]
    fp = os.path.join(OUT, "%s.csv" % short)
    if os.path.exists(fp):
        skip += 1
        continue
    done = False
    retry = 0
    while retry < 3:
        try:
            resp = requests.post(URL, headers=HDR, data={
                "bld": "dbms/MDC/STAT/standard/MDCSTAT02302",
                "strtDd": START,
                "endDd": END,
                "isuCd": isin,
                "inqTpCd": "2",
                "trdVolVal": "2",
                "askBid": "3",
            }, timeout=30)
            out = resp.json().get("output", [])
            if out:
                keys = list(out[0].keys())
                with open(fp, "w", newline="", encoding="utf-8-sig") as f:
                    wr = csv.DictWriter(f, fieldnames=keys)
                    wr.writeheader()
                    wr.writerows(out)
                ok += 1
            else:
                fail += 1
            done = True
            break
        except Exception as e:
            retry += 1
            log("RETRY %s (%d): %s" % (short, retry, str(e)[:60]))
            time.sleep(30)
    if not done:
        fail += 1
        log("FAIL %s" % short)
    if i % 50 == 0:
        log("%d/%d ok=%d skip=%d fail=%d" % (i, len(items), ok, skip, fail))
    time.sleep(1.0)

log("DONE ok=%d skip=%d fail=%d" % (ok, skip, fail))
