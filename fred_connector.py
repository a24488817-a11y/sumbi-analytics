import requests, os
from dotenv import load_dotenv

load_dotenv()
FRED_KEY = os.environ.get("FRED_API_KEY")

def get_fred_series(series_id):
    try:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {"series_id": series_id, "api_key": FRED_KEY,
                  "file_type": "json", "limit": 1, "sort_order": "desc"}
        r = requests.get(url, params=params, timeout=10)
        val = r.json()["observations"][0]["value"]
        return float(val) if val != "." else None
    except:
        return None

def get_macro_fred():
    return {
        "ffr": get_fred_series("FEDFUNDS"),
        "tnx": get_fred_series("DGS10"),
        "cpi": get_fred_series("CPIAUCSL"),
        "vix": get_fred_series("VIXCLS"),
        "krw": get_fred_series("DEXKOUS"),
        "wti": get_fred_series("DCOILWTICO"),
    }

if __name__ == "__main__":
    data = get_macro_fred()
    print("FRED 매크로:")
    for k, v in data.items():
        print(f"  {k}: {v}")
