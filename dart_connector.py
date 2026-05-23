import requests, os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from functools import lru_cache

load_dotenv()
DART_KEY = os.environ.get("DART_API_KEY")

@lru_cache(maxsize=500)
def get_corp_code(ticker):
    try:
        import zipfile, io, xml.etree.ElementTree as ET
        url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={DART_KEY}"
        r = requests.get(url, timeout=15)
        zf = zipfile.ZipFile(io.BytesIO(r.content))
        xml_data = zf.read("CORPCODE.xml")
        root = ET.fromstring(xml_data)
        for corp in root.findall("list"):
            stock = corp.findtext("stock_code", "").strip()
            if stock == ticker:
                return corp.findtext("corp_code", "").strip()
    except Exception as e:
        print(f"corp_code 오류: {e}")
    return None

def get_dart_disclosures(ticker, days=3):
    try:
        corp_code = get_corp_code(ticker)
        if not corp_code:
            return []
        start = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        end = datetime.now().strftime("%Y%m%d")
        params = {"crtfc_key": DART_KEY, "corp_code": corp_code,
                  "bgn_de": start, "end_de": end, "sort": "date",
                  "sort_mth": "desc", "page_count": 10}
        r = requests.get("https://opendart.fss.or.kr/api/list.json", params=params, timeout=10)
        data = r.json()
        if data.get("status") != "000":
            return []
        return [{ "title": i.get("report_nm",""), "date": i.get("rcept_dt","") } for i in data.get("list",[])]
    except Exception as e:
        print(f"DART 공시 오류: {e}")
        return []

def calc_dart_score(ticker):
    disclosures = get_dart_disclosures(ticker)
    if not disclosures:
        return 2, {}
    score = 2
    positive = ["자사주","배당","수주","계약","자기주식취득"]
    negative = ["횡령","배임","조사","상장폐지","감사의견","과징금"]
    titles = []
    for d in disclosures[:5]:
        t = d["title"]
        titles.append(t[:15])
        if any(k in t for k in positive): score += 1
        if any(k in t for k in negative): score -= 2
    return max(0, min(score, 5)), {"공시수": len(disclosures), "최근": titles}

if __name__ == "__main__":
    print("삼성전자 테스트:")
    s, d = calc_dart_score("005930")
    print(f"점수: {s}/5, {d}")
