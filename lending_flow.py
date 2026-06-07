#!/usr/bin/env python3
import os, sys, csv, time, requests
from datetime import datetime, timedelta

OUT_DIR = os.path.expanduser("~/sumbi-analytics/lending_data")
os.makedirs(OUT_DIR, exist_ok=True)
FIELDS = ["stck_bsop_date", "loan_deal", "loan_repay", "loan_balance"]
URL = "https://m.seibro.or.kr/cnts/loan/selectStockLoanDeal.do"
HDRS = {"User-Agent": "Mozilla/5.0", "Referer": "https://m.seibro.or.kr"}


def log(m):
    print("[%s] %s" % (datetime.now().strftime("%H:%M:%S"), m), flush=True)


def clean(v):
    return str(v).replace(",", "").strip()


def existing_dates(fp):
    dates = set()
    if not os.path.exists(fp):
        return dates
    try:
        with open(fp, "r", newline="") as f:
            for row in csv.DictReader(f):
                dt = (row.get("stck_bsop_date") or "").strip()
                if dt:
                    dates.add(dt)
    except Exception:
        pass
    return dates


def append_row(fp, row):
    new_file = not os.path.exists(fp) or os.path.getsize(fp) == 0
    with open(fp, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        w.writerow(row)


def get_universe():
    try:
        import FinanceDataReader as fdr
        df = fdr.StockListing("KRX")
        col = "Code" if "Code" in df.columns else df.columns[0]
        codes = [str(c).zfill(6) for c in df[col].tolist()]
        codes = [c for c in codes if c.isdigit() and len(c) == 6]
        if codes:
            return sorted(set(codes))
    except Exception as e:
        log("fdr failed (%s), fallback to CSV filenames" % type(e).__name__)
    base = os.path.expanduser("~/sumbi-analytics/kis_stock_data")
    src = base if os.path.isdir(base) else OUT_DIR
    codes = [fn[:-4] for fn in os.listdir(src) if fn.endswith(".csv")]
    return sorted(set(codes))


def fetch_lending(ticker, from_dt, to_dt):
    import pandas as pd
    try:
        r = requests.post(URL, data={"isin": ticker, "fromDt": from_dt, "toDt": to_dt},
                          headers=HDRS, timeout=10)
        if r.status_code != 200:
            return None
        df = pd.read_html(r.content, encoding="utf-8")[0]
        rows = []
        for _, x in df.iterrows():
            v = x.tolist()
            if len(v) < 4:
                continue
            dt = clean(v[0]).replace("-", "/")
            if not dt or not dt[0].isdigit():
                continue
            rows.append({"stck_bsop_date": dt,
                         "loan_deal": clean(v[1]),
                         "loan_repay": clean(v[2]),
                         "loan_balance": clean(v[3])})
        return rows
    except Exception:
        return None


def main():
    args = sys.argv[1:]
    limit = None
    single = None
    if "--limit" in args:
        i = args.index("--limit")
        try:
            limit = int(args[i + 1])
        except Exception:
            limit = None
    elif args and args[0].isdigit():
        single = args[0].zfill(6)

    today = datetime.now().strftime("%Y%m%d")
    d10 = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")

    if single:
        tickers = [single]
    else:
        tickers = get_universe()
        if limit:
            tickers = tickers[:limit]
    log("lending start"); log("universe: %d" % len(tickers))

    ok = skip = fail = empty = 0
    for i, t in enumerate(tickers, 1):
        fp = os.path.join(OUT_DIR, "%s.csv" % t)
        rows = fetch_lending(t, d10, today)
        if rows is None:
            fail += 1
        elif not rows:
            empty += 1
        else:
            have = existing_dates(fp)
            added = 0
            for row in rows:
                if row["stck_bsop_date"] in have:
                    continue
                try:
                    append_row(fp, row); added += 1
                except Exception:
                    pass
            if added:
                ok += 1
            else:
                skip += 1
        time.sleep(0.3)
        if i % 200 == 0:
            log("progress %d/%d ok=%d skip=%d empty=%d fail=%d" %
                (i, len(tickers), ok, skip, empty, fail))
    log("DONE total=%d ok=%d skip=%d empty=%d fail=%d" %
        (len(tickers), ok, skip, empty, fail))


if __name__ == "__main__":
    main()
