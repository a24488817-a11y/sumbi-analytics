#!/usr/bin/env python3
import os,sys,csv,time,requests
from datetime import datetime
try:
 from dotenv import load_dotenv;load_dotenv(os.path.expanduser("~/.env"))
except:pass
APP_KEY=os.environ.get("KIS_APP_KEY");APP_SECRET=os.environ.get("KIS_APP_SECRET")
URL_BASE="https://openapi.koreainvestment.com:9443"
OUT_DIR=os.path.expanduser("~/sumbi-analytics/credit_data");os.makedirs(OUT_DIR,exist_ok=True)
FIELDS=["stck_bsop_date","whol_loan_rmnd_rate","marg_rate","crdt_able_yn"]
def log(m):print("[%s] %s"%(datetime.now().strftime("%H:%M:%S"),m),flush=True)
def clean(v):return str(v).replace(",","").strip()
def get_token():
 if not APP_KEY or not APP_SECRET:log("ERROR:keys not found");sys.exit(1)
 try:
  res=requests.post(URL_BASE+"/oauth2/tokenP",json={"grant_type":"client_credentials","appkey":APP_KEY,"appsecret":APP_SECRET},timeout=10).json()
  tok=res.get("access_token")
  if not tok:log("ERROR:no tok");sys.exit(1)
  return tok
 except Exception as e:log("ERR:%s"%(type(e).__name__,));sys.exit(1)
def fetch_credit(token,ticker):
 try:
  today=datetime.now().strftime("%Y%m%d")
  out=requests.get(URL_BASE+"/uapi/domestic-stock/v1/quotations/inquire-price",headers={"authorization":"Bearer "+token,"appkey":APP_KEY,"appsecret":APP_SECRET,"tr_id":"FHKST01010100"},params={"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":ticker},timeout=10).json().get("output",{})
  if not out:return None
  return{"stck_bsop_date":today,"whol_loan_rmnd_rate":clean(out.get("whol_loan_rmnd_rate","0")),"marg_rate":clean(out.get("marg_rate","0")),"crdt_able_yn":clean(out.get("crdt_able_yn","N"))}
 except:return None
def existing_dates(fp):
    dates=set()
    if not os.path.exists(fp):return dates
    try:
        with open(fp,"r",newline="") as f:
            for row in csv.DictReader(f):
                dt=(row.get("stck_bsop_date") or "").strip()
                if dt:dates.add(dt)
    except:pass
    return dates
def append_row(fp,row):
    nf=not os.path.exists(fp) or os.path.getsize(fp)==0
    with open(fp,"a",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS)
        if nf:w.writeheader()
        w.writerow(row)

def get_universe():
 try:
  import FinanceDataReader as fdr;df=fdr.StockListing("KRX")
  col="Code" if "Code" in df.columns else df.columns[0]
  codes=[str(c).zfill(6) for c in df[col].tolist()]
  codes=[c for c in codes if c.isdigit() and len(c)==6]
  if codes:return sorted(set(codes))
 except Exception as e:log("fdr failed(%s)"%type(e).__name__)
 base=os.path.expanduser("~/sumbi-analytics/kis_stock_data")
 src=base if os.path.isdir(base) else OUT_DIR
 return sorted(set([fn[:-4] for fn in os.listdir(src) if fn.endswith(".csv")]))
def main():
 args=sys.argv[1:];limit=None;single=None
 if "--limit" in args:
  i=args.index("--limit")
  try:limit=int(args[i+1])
  except:limit=None
 elif args and args[0].isdigit():single=args[0].zfill(6)
 log("credit start");token=get_token();log("token OK")
 tickers=[single] if single else get_universe()
 if limit:tickers=tickers[:limit]
 log("universe:%d"%len(tickers));ok=skip=fail=empty=0
 for i,t in enumerate(tickers,1):
  fp=os.path.join(OUT_DIR,"%s.csv"%t)
  row=fetch_credit(token,t)
  if row is None:empty+=1
  else:
   dt=row["stck_bsop_date"]
   if not dt:empty+=1
   elif dt in existing_dates(fp):skip+=1
   else:
    try:append_row(fp,row);ok+=1
    except:fail+=1
  time.sleep(0.06)
  if i%200==0:log("progress %d/%d ok=%d skip=%d empty=%d fail=%d"%(i,len(tickers),ok,skip,empty,fail))
 log("DONE total=%d ok=%d skip=%d empty=%d fail=%d"%(len(tickers),ok,skip,empty,fail))
if __name__=="__main__":
 main()
