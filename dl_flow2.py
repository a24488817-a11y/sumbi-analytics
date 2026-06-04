import requests, os, time, csv
from datetime import datetime

OUT = os.path.expanduser("~/data/kosdaq_flow")
os.makedirs(OUT, exist_ok=True)
START = "20150101"
END = "20260602"

# KRX 방화벽을 뚫기 위한 완벽한 사람 위장 헤더
HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "http://data.krx.co.kr/contents/MDC/STAT/standard/MDCSTAT02301.jsp"
}

def log(m):
    print("[%s] %s" % (datetime.now().strftime("%H:%M:%S"), m), flush=True)

log("Fetching KOSDAQ list...")
with requests.Session() as s:
    s.headers.update(HDR)
    
    # 1. 코스닥 종목 리스트 확보
    r = s.post("http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd", data={
        "bld": "dbms/comm/finder/finder_stkisu",
        "mktsel": "KSQ",
        "typeNo": "0",
    }, timeout=30)
    items = r.json().get("block1", [])
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
                # 2. 핵심: 매 종목마다 OTP 토큰을 정식으로 발급받아 우회
                otp_res = s.post("http://data.krx.co.kr/comm/bldAttendant/getOtpData.cmd", data={
                    "bld": "dbms/MDC/STAT/standard/MDCSTAT02302"
                }, timeout=30)
                otp = otp_res.text
                
                # 3. OTP 토큰을 첨부하여 실제 수급 데이터 10년 치 요청
                resp = s.post("http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd", data={
                    "bld": "dbms/MDC/STAT/standard/MDCSTAT02302",
                    "strtDd": START,
                    "endDd": END,
                    "isuCd": isin,
                    "inqTpCd": "2",
                    "trdVolVal": "2",
                    "askBid": "3",
                    "code": otp
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
                time.sleep(1.0) # 차단 방지를 위한 1초 휴식
                break
            except Exception as e:
                retry += 1
                log("RETRY %s (%d)" % (short, retry))
                time.sleep(10) # 에러 시 10초 대기 후 재시도
                
        if not done:
            fail += 1
            log("FAIL %s" % short)
            
        if i % 10 == 0:
            log("%d/%d ok=%d skip=%d fail=%d" % (i, len(items), ok, skip, fail))

log("DONE ok=%d skip=%d fail=%d" % (ok, skip, fail))
