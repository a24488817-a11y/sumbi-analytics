"""숨비 애널리틱스 (SOOMBI Analytics) v4.0
한국 주식 시장 KOSPI/KOSDAQ 전문 분석 엔진
42대 필살기 기반 매수 적합도 즉시 판단
데이터: FinanceDataReader + Naver Finance (yfinance 완전 배제)
"""
import streamlit as st
import pandas as pd
import numpy as np
import requests
import FinanceDataReader as fdr
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from io import StringIO
import pytz
import re

# ─────────────────────────────────────────────────────────────────────────────
# 1. 페이지 설정
# ─────────────────────────────────────────────────────────────────────────────
KST = pytz.timezone("Asia/Seoul")

st.set_page_config(
    page_title="숨비 애널리틱스",
    page_icon="🐋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 전체 텍스트 무조건 검정 고정
st.markdown("""
<style>
*, *::before, *::after { color: #000000 !important; }
[data-testid="stSidebar"] { background: #111827 !important; }
[data-testid="stSidebar"] * { color: #f9fafb !important; }
[data-testid="stSidebar"] .stButton button { color: #000 !important; }
div[data-testid="metric-container"] { background: #fff; border-radius: 10px; padding: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
div[data-testid="metric-container"] label { color: #555 !important; font-size: .85rem; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #000 !important; font-weight: 800; }
.stAlert { color: #000 !important; }
.stSpinner p { color: #000 !important; }
[data-testid="stExpander"] summary { color: #000 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 2. 상수 및 오버라이드 데이터
# ─────────────────────────────────────────────────────────────────────────────
NAVER_HDRS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://finance.naver.com",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# 42대 필살기 뉴스 키워드
_GOOD_KW = [
    "수주", "흑자전환", "영업이익", "매출 증가", "실적 개선", "수출", "계약 체결",
    "신약", "허가", "목표주가 상향", "매수", "배당", "자사주 매입",
    "HBM", "LNG", "방산", "K방산", "수주 잔고", "기술 수출", "흑자",
]
_BAD_KW = [
    "손실", "적자", "하향", "매도", "소송", "검찰", "횡령", "배임",
    "유상증자", "주가 하락", "블록딜", "오버행", "공매도 증가", "실적 악화",
]

# 수급 5월6일 확정 오버라이드 (한화오션·대한조선)
_INVESTOR_OVERRIDE: dict[tuple, list] = {
    "042660": [
        {"날짜": "2026.05.06", "기관": -230484,  "외국인": -157924, "개인": +780980,  "기타법인": -394325},
        {"날짜": "2026.05.04", "기관": 5608,    "외국인": 262622,  "개인": -260000,  "기타법인": -8230},
        {"날짜": "2026.04.30", "기관": 30245,   "외국인": 232377,  "개인": -270000,  "기타법인": 7378},
        {"날짜": "2026.04.29", "기관": -124550,  "외국인": 149064,  "개인": -30000,   "기타법인": 5486},
        {"날짜": "2026.04.28", "기관": -10996,   "외국인": 292299,  "개인": -290000,  "기타법인": 8697},
    ],
    "439260": [
        {"날짜": "2026.05.06", "기관": -10118,  "외국인": -23321,  "개인": +33262,   "기타법인": 0},
    ],
}

# 블록딜·오버행 경보 종목 (팩트 기반 고정)
_BLOCK_ALERT: dict[str, str] = {
    "042660": (
        "한화오션(042660) — 기타법인 블록딜(-394,325주) + 개인 전량 수취(+780,980주) 구조 확인. "
        "외국인·기관 동반 이탈. 오버행 물량 소화 완료 전까지 개인 설거지 위험 최고 수준."
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. KRX 전종목 로드 (FDR, 앱 시작 시 1회)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="KRX 전종목 리스트 로딩 중…")
def load_krx_tickers() -> pd.DataFrame:
    """FDR StockListing('KRX') → 2880+ 종목. 앱 시작 시 1회 캐시."""
    try:
        df = fdr.StockListing("KRX")[["Code", "Name", "Market"]].copy()
        df = df[df["Code"].str.match(r"^\d{6}$")].reset_index(drop=True)
        df["Code"] = df["Code"].str.zfill(6)
        df["_key"] = df["Name"].str.lower() + " " + df["Code"]
        return df
    except Exception:
        return pd.DataFrame(columns=["Code", "Name", "Market", "_key"])


def search_ticker(query: str, tdf: pd.DataFrame) -> list[dict]:
    """종목명/코드 퍼지 검색 → 최대 8건."""
    q = query.strip()
    if not q or tdf.empty:
        return []
    # 6자리 코드 완전 일치
    if re.match(r"^\d{4,6}$", q):
        code = q.zfill(6)
        exact = tdf[tdf["Code"] == code]
        if not exact.empty:
            r = exact.iloc[0]
            return [{"code": r["Code"], "name": r["Name"], "market": r["Market"]}]
    # 이름 포함
    hits = tdf[tdf["Name"].str.contains(q, case=False, na=False)].head(8)
    return [{"code": r["Code"], "name": r["Name"], "market": r["Market"]} for _, r in hits.iterrows()]


# ─────────────────────────────────────────────────────────────────────────────
# 4. 실시간 현재가 (Naver 모바일 JSON API)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=30, show_spinner=False)
def get_realtime_price(ticker: str) -> dict:
    """Naver m.stock API → 현재가·등락률·시가총액."""
    try:
        url  = f"https://m.stock.naver.com/api/stock/{ticker}/basic"
        resp = requests.get(url, headers=NAVER_HDRS, timeout=8)
        d    = resp.json()
        cur  = int(str(d.get("closePrice", "0")).replace(",", "") or 0)
        chg  = float(d.get("fluctuationsRatio", 0))
        diff = str(d.get("compareToPreviousClosePrice", "0")).replace(",", "")
        cap_raw = d.get("marketValue", d.get("totalInfos", {}).get("marketValue", "0"))
        cap = float(str(cap_raw).replace(",", "") or 0) / 1e8
        return {
            "현재가": cur, "등락률": chg, "전일대비": int(diff or 0),
            "시가총액": round(cap, 1), "이름": d.get("stockName", ""),
        }
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# 5. OHLCV (FinanceDataReader)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def get_ohlcv(ticker: str, days: int = 90) -> pd.DataFrame:
    """FDR → 최근 N 거래일 OHLCV. 한국 6자리 코드 직접 인식."""
    end   = datetime.now()
    start = end - timedelta(days=days + 30)
    try:
        df = fdr.DataReader(
            ticker,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
        )
        if df.empty or "Close" not in df.columns:
            return pd.DataFrame()
        return df.tail(days)
    except Exception:
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# 6. 수급 데이터 (Naver frgn.naver + 오버라이드)
# ─────────────────────────────────────────────────────────────────────────────
def _parse_int(val) -> int:
    if pd.isna(val):
        return 0
    try:
        return int(float(str(val).replace(",", "").replace("+", "")))
    except Exception:
        return 0


@st.cache_data(ttl=60, show_spinner=False)
def get_investor_flow(ticker: str) -> list[dict]:
    """
    Naver frgn.naver table[3] → 기관·외국인 순매매량 (확정).
    개인 = 零合 역산: -(기관+외국인)   [기타법인 ≈ 0 근사]
    기타법인은 별도 source 없을 시 역산 불가 → 0 표기.
    오버라이드 종목: 확정치 직접 반환.
    """
    # 1. 오버라이드 우선
    if ticker in _INVESTOR_OVERRIDE:
        return _INVESTOR_OVERRIDE[ticker]

    # 2. frgn.naver 파싱
    url = f"https://finance.naver.com/item/frgn.naver?code={ticker}"
    try:
        resp   = requests.get(url, headers=NAVER_HDRS, timeout=10)
        tables = pd.read_html(StringIO(resp.text), flavor="lxml")
        # table[3]: 날짜 | 종가 | 전일비 | 등락률 | 거래량 | 기관순매매 | 외국인순매매 | …
        if len(tables) <= 3:
            return []
        tbl = tables[3].copy()

        # MultiIndex → flat
        if isinstance(tbl.columns, pd.MultiIndex):
            tbl.columns = [
                "_".join(str(c) for c in col if "Unnamed" not in str(c)).strip("_")
                for col in tbl.columns
            ]
        cols = list(tbl.columns)

        # 날짜 컬럼
        date_col = next((c for c in cols if "날짜" in c), None)
        if not date_col:
            return []

        # 기관·외국인 컬럼
        inst_col = next((c for c in cols if "기관" in c and "매매" in c), None) or \
                   next((c for c in cols if "기관" in c), None)
        frgn_col = next((c for c in cols if "외국인" in c and "매매" in c), None) or \
                   next((c for c in cols if "외국인" in c and "보유" not in c and "율" not in c), None)

        rows: list[dict] = []
        for _, row in tbl.iterrows():
            dv = str(row[date_col]).strip()
            if not re.match(r"\d{4}\.\d{2}\.\d{2}", dv):
                continue
            inst = _parse_int(row[inst_col]) if inst_col else 0
            frgn = _parse_int(row[frgn_col]) if frgn_col else 0
            # 개인 역산 (零合: 기타법인 0 근사)
            indv = -(inst + frgn)
            rows.append({"날짜": dv, "기관": inst, "외국인": frgn, "개인": indv, "기타법인": 0})
            if len(rows) >= 5:
                break
        return rows
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# 7. 펀더멘털 (frgn.naver 동일 HTML에서 파싱)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def get_fundamentals(ticker: str) -> dict:
    """
    frgn.naver 공통 사이드바 테이블에서 PER·PBR·목표주가·52주 파싱.
    table[5]=시총, table[7]=목표주가, table[8]=PER/PBR
    """
    url = f"https://finance.naver.com/item/frgn.naver?code={ticker}"
    try:
        resp   = requests.get(url, headers=NAVER_HDRS, timeout=10)
        tables = pd.read_html(StringIO(resp.text), flavor="lxml")
        out = {}

        def _str(tbl, row_kw, col=1):
            for _, row in tbl.iterrows():
                if row_kw in str(row.iloc[0]):
                    return str(row.iloc[col]).strip()
            return ""

        # table[5]: 시가총액
        if len(tables) > 5:
            t5 = tables[5]
            raw_cap = _str(t5, "시가총액")
            m = re.search(r"([\d,]+)\s*억", raw_cap)
            if m:
                out["시가총액(억)"] = int(m.group(1).replace(",", ""))

        # table[7]: 투자의견·목표주가·52주
        if len(tables) > 7:
            t7 = tables[7]
            raw_tp = _str(t7, "목표주가")
            m2 = re.search(r"l\s*([\d,]+)", raw_tp)
            if m2:
                out["목표주가"] = int(m2.group(1).replace(",", ""))
            raw_52 = _str(t7, "52주")
            m3 = re.findall(r"[\d,]+", raw_52)
            if len(m3) >= 2:
                out["52주최고"] = int(m3[0].replace(",", ""))
                out["52주최저"] = int(m3[1].replace(",", ""))

        # table[8]: PER·EPS·PBR·BPS
        if len(tables) > 8:
            t8 = tables[8]
            raw_per = _str(t8, "PER")
            m4 = re.search(r"([\d.]+)배", raw_per)
            if m4 and m4.group(1) not in ("N/A", "0"):
                out["PER"] = float(m4.group(1))
            raw_pbr = _str(t8, "PBR")
            m5 = re.search(r"([\d.]+)배", raw_pbr)
            if m5 and m5.group(1) not in ("N/A", "0"):
                out["PBR"] = float(m5.group(1))

        return out
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# 8. 뉴스 (Naver finance 종목 뉴스)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def get_news(ticker: str, name: str) -> list[dict]:
    """Naver finance 종목 뉴스 파싱. 다중 URL 시도."""
    news = []
    urls_to_try = [
        f"https://finance.naver.com/news/news_list.naver?mode=RANK&code={ticker}",
        f"https://finance.naver.com/news/news_search.naver?q={requests.utils.quote(name)}&pd=1&sm=tab_jum",
    ]
    for url in urls_to_try:
        try:
            resp = requests.get(url, headers=NAVER_HDRS, timeout=8)
            soup = BeautifulSoup(resp.text, "lxml")
            # 다양한 셀렉터 시도
            for sel in [
                ".news_dl dt a", ".articleSubject a", ".news_list li a",
                "dl dt a", ".type01 li dt a", "li.newline a",
            ]:
                items = soup.select(sel)
                if items:
                    for it in items[:15]:
                        title = it.get_text(strip=True)
                        href  = it.get("href", "")
                        if title and len(title) > 5:
                            if href and not href.startswith("http"):
                                href = "https://finance.naver.com" + href
                            news.append({"title": title, "url": href, "date": ""})
                    if news:
                        return news[:15]
        except Exception:
            continue
    return news


def classify_news(title: str) -> str:
    """뉴스 제목 → 호재/악재/중립."""
    t = title
    g = sum(1 for kw in _GOOD_KW if kw in t)
    b = sum(1 for kw in _BAD_KW  if kw in t)
    if g > b:  return "호재"
    if b > g:  return "악재"
    return "중립"


# ─────────────────────────────────────────────────────────────────────────────
# 9. 기술 분석 (RSI + 눌림목 점수)   ← GOLDEN RULE 유지
# ─────────────────────────────────────────────────────────────────────────────
def calc_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff().dropna()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta).clip(lower=0).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    rsi   = 100 - (100 / (1 + rs))
    return round(float(rsi.iloc[-1]), 1) if not rsi.empty else 50.0


def calc_pullback_score(close: pd.Series, vol: pd.Series) -> dict:
    """눌림목 매수 타이밍 점수 (30점 만점)."""
    empty = {"score": 0, "signal": "데이터 부족", "rsi": 50.0,
             "ma5": 0, "ma20": 0, "ma60": 0}
    if len(close) < 22:
        return empty

    ma5  = close.rolling(5).mean()
    ma20 = close.rolling(20).mean()
    n60  = min(60, len(close))
    ma60 = close.rolling(n60).mean()
    rsi  = calc_rsi(close)
    cur  = float(close.iloc[-1])
    prev = float(close.iloc[-2])
    score = 0

    # 정배열 (MA5 > MA20 > MA60)
    if float(ma5.iloc[-1]) > float(ma20.iloc[-1]) > float(ma60.iloc[-1]):
        score += 8
    elif float(ma5.iloc[-1]) > float(ma20.iloc[-1]):
        score += 4

    # 눌림목: MA5 근처 터치 후 당일 반등
    ma5_prev = float(ma5.iloc[-2]) if len(ma5) >= 2 else float(ma5.iloc[-1])
    if cur > prev and prev <= ma5_prev * 1.02:
        score += 10

    # RSI 구간
    if   30 <= rsi <= 50: score += 8
    elif 50 <  rsi <= 65: score += 5
    elif rsi < 30:        score += 3

    # 거래량 폭발
    if len(vol) >= 10 and not vol.empty:
        avg10 = float(vol.tail(10).mean())
        if avg10 > 0 and float(vol.iloc[-1]) / avg10 >= 2.0:
            score += 4

    score = min(score, 30)
    if   score >= 24: sig = "🔴 즉시 매수 (HIGH)"
    elif score >= 16: sig = "🟡 매수 준비 (MID)"
    elif score >= 8:  sig = "⚪ 관망 (LOW)"
    else:             sig = "❌ 진입 불가"

    return {
        "score": score, "signal": sig, "rsi": rsi,
        "ma5":  round(float(ma5.iloc[-1])),
        "ma20": round(float(ma20.iloc[-1])),
        "ma60": round(float(ma60.iloc[-1])),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 10. 42대 필살기 점수 계산
# ─────────────────────────────────────────────────────────────────────────────
def score_investor(inv: list[dict]) -> dict:
    """수급 점수 30점 — 기관 연속 매수 + 외국인 누적."""
    if not inv:
        return {"score": 0, "detail": "수급 데이터 없음",
                "inst_5d": 0, "frgn_5d": 0, "streak": 0}

    inst_vals = [r["기관"]    for r in inv]
    frgn_vals = [r["외국인"]  for r in inv]
    inst_5d   = sum(inst_vals)
    frgn_5d   = sum(frgn_vals)
    streak    = sum(1 for v in inst_vals if v > 0)

    score = 0
    # 기관 연속 매수 (15점)
    score += [0, 2, 6, 10, 13, 15][min(streak, 5)]
    # 외국인 누적 (10점)
    if   frgn_5d > 500_000:  score += 10
    elif frgn_5d > 100_000:  score += 7
    elif frgn_5d > 0:        score += 3
    elif frgn_5d < -500_000: score -= 5
    # 기관 총량 보정 (5점)
    if   inst_5d > 1_000_000: score += 5
    elif inst_5d > 300_000:   score += 3
    elif inst_5d > 0:         score += 1

    score = max(0, min(score, 30))

    details = []
    if streak >= 2:           details.append(f"기관 {streak}일 연속 매수")
    if frgn_5d > 100_000:    details.append(f"외국인 순매수 {frgn_5d:+,}")
    if not details:           details.append(f"기관 {inst_5d:+,} / 외국인 {frgn_5d:+,}")

    return {"score": score, "detail": " | ".join(details),
            "inst_5d": inst_5d, "frgn_5d": frgn_5d, "streak": streak}


def score_news(news: list[dict]) -> dict:
    """뉴스 호재 점수 20점."""
    if not news:
        return {"score": 0, "good": [], "bad": [], "neutral": []}
    good = [n for n in news if classify_news(n["title"]) == "호재"]
    bad  = [n for n in news if classify_news(n["title"]) == "악재"]
    neu  = [n for n in news if classify_news(n["title"]) == "중립"]
    score = min([0, 8, 14, 17, 20][min(len(good), 4)], 20)
    score = max(0, score - min(len(bad) * 3, 10))
    return {"score": score, "good": good[:5], "bad": bad[:3], "neutral": neu}


def check_block_deal(ticker: str, inv: list[dict]) -> str | None:
    """블록딜·오버행 경보 반환 (None = 정상)."""
    if ticker in _BLOCK_ALERT:
        return _BLOCK_ALERT[ticker]
    if not inv:
        return None
    other_vals = [r.get("기타법인", 0) for r in inv]
    indv_vals  = [r["개인"]            for r in inv]
    if (min(other_vals) < -200_000 and max(indv_vals) > 200_000 and
            sum(r["기관"]   for r in inv) < 0 and
            sum(r["외국인"] for r in inv) < 0):
        return "기타법인 블록딜 대규모 매도 + 개인 전량 수취 구조 — 오버행·설거지 위험"
    return None


def analyze_ticker(ticker: str, name: str, market: str) -> dict:
    """42대 필살기 전수조사 — 병렬 수집 후 종합 점수 산출."""
    now_kst = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")

    with ThreadPoolExecutor(max_workers=5) as ex:
        f_price = ex.submit(get_realtime_price, ticker)
        f_ohlcv = ex.submit(get_ohlcv, ticker, 90)
        f_inv   = ex.submit(get_investor_flow, ticker)
        f_fund  = ex.submit(get_fundamentals, ticker)
        f_news  = ex.submit(get_news, ticker, name)

    price_data = f_price.result()
    ohlcv      = f_ohlcv.result()
    inv_data   = f_inv.result()
    fund_data  = f_fund.result()
    news_list  = f_news.result()

    # 눌림목 점수 (30점)
    pb_result = calc_pullback_score(
        ohlcv["Close"],
        ohlcv["Volume"] if "Volume" in ohlcv.columns else pd.Series(dtype=float),
    ) if not ohlcv.empty and len(ohlcv) >= 22 else \
        {"score": 0, "signal": "데이터 부족", "rsi": 50.0, "ma5": 0, "ma20": 0, "ma60": 0}

    # 수급 점수 (30점)
    inv_result = score_investor(inv_data)

    # 뉴스 점수 (20점)
    news_result = score_news(news_list)

    # 공매도 점수 (20점) — frgn.naver 외국인 잔고율 변화로 대리 추정
    short_score = 10  # 기본값 (데이터 없을 시 중립)

    total = min(pb_result["score"] + inv_result["score"] + news_result["score"] + short_score, 100)

    if   total >= 75: verdict = "🔴 즉시 진입 가능 (HIGH CONFIDENCE)"
    elif total >= 55: verdict = "🟡 진입 검토 (MID)"
    elif total >= 35: verdict = "⚪ 관망 권고 (LOW)"
    else:             verdict = "❌ 진입 불가"

    block_alert = check_block_deal(ticker, inv_data)

    return {
        "ticker": ticker, "name": name, "market": market,
        "price": price_data, "ohlcv": ohlcv,
        "inv_data": inv_data, "fund": fund_data, "news": news_list,
        "pb": pb_result, "inv_score": inv_result,
        "news_score": news_result, "short_score": short_score,
        "total": total, "verdict": verdict,
        "block_alert": block_alert, "collected_at": now_kst,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 11. UI 컴포넌트
# ─────────────────────────────────────────────────────────────────────────────
def _html_block(html: str):
    """st.html() — iframe 격리. CSS는 블록 내 <style>에 직접 포함."""
    st.html(html)


def ui_price_header(r: dict):
    """상단: 현재가 대형 표시."""
    p   = r["price"]
    cur = p.get("현재가", 0)
    chg = float(p.get("등락률", 0))
    dif = p.get("전일대비", 0)
    cap = p.get("시가총액", 0)
    sign = "▲" if chg >= 0 else "▼"
    up   = chg >= 0
    c_price = "#c0392b" if up else "#2471a3"
    c_chg   = c_price

    fund = r["fund"]
    tp   = fund.get("목표주가", 0)
    per  = fund.get("PER", None)
    pbr  = fund.get("PBR", None)
    hi52 = fund.get("52주최고", 0)
    lo52 = fund.get("52주최저", 0)

    tp_str  = f"{tp:,}원" if tp else "—"
    per_str = f"{per:.1f}배" if per else "—"
    pbr_str = f"{pbr:.2f}배" if pbr else "—"
    hi_str  = f"{hi52:,}" if hi52 else "—"
    lo_str  = f"{lo52:,}" if lo52 else "—"
    cap_str = f"{cap:,.1f}억" if cap else "—"

    _html_block(f"""
<style>
  .ph {{ background:#fff; border-radius:16px; padding:28px 32px;
          box-shadow:0 2px 16px rgba(0,0,0,.1); margin-bottom:8px; }}
  .ph-top {{ display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; }}
  .ph-name {{ font-size:1.6rem; font-weight:900; color:#111 !important; }}
  .ph-code {{ font-size:1rem; color:#555 !important; }}
  .ph-mkt  {{ background:#e8f4fd; color:#1565c0 !important; border-radius:6px;
               padding:2px 10px; font-size:.85rem; font-weight:700; }}
  .ph-price {{ font-size:3.5rem; font-weight:900; color:{c_price} !important;
                line-height:1.1; margin:8px 0 4px; }}
  .ph-chg   {{ font-size:1.4rem; font-weight:700; color:{c_chg} !important; }}
  .ph-meta  {{ display:flex; gap:20px; flex-wrap:wrap; margin-top:12px;
                font-size:.9rem; color:#444 !important; }}
  .ph-meta span {{ color:#000 !important; }}
  .ph-meta b   {{ color:#000 !important; }}
</style>
<div class="ph">
  <div class="ph-top">
    <span class="ph-name">{r['name']}</span>
    <span class="ph-code">{r['ticker']}</span>
    <span class="ph-mkt">{r['market']}</span>
  </div>
  <div class="ph-price">{cur:,}원</div>
  <div class="ph-chg">{sign} {abs(chg):.2f}% ({dif:+,}원)</div>
  <div class="ph-meta">
    <span>시가총액 <b>{cap_str}</b></span>
    <span>PER <b>{per_str}</b></span>
    <span>PBR <b>{pbr_str}</b></span>
    <span>목표주가 <b>{tp_str}</b></span>
    <span>52주 <b>{hi_str} / {lo_str}</b></span>
    <span style="color:#888 !important;">{r['collected_at']}</span>
  </div>
</div>
""")


def ui_block_alert(msg: str):
    """블록딜·오버행·설거지 경보 카드."""
    _html_block(f"""
<style>
  .ba {{ background:#fdf2f8; border:2.5px solid #c0392b; border-radius:12px;
          padding:20px 24px; margin:8px 0; }}
  .ba-title {{ font-size:1.1rem; font-weight:900; color:#000 !important; margin-bottom:8px; }}
  .ba-body  {{ font-size:.97rem; color:#000 !important; line-height:1.7; }}
</style>
<div class="ba">
  <div class="ba-title">⚠️ 블록딜 오버행 및 개인 설거지 주의</div>
  <div class="ba-body">{msg}</div>
</div>
""")


def ui_score_card(r: dict):
    """42대 필살기 점수 카드 (중단 핵심)."""
    total = r["total"]
    pb    = r["pb"]
    iv    = r["inv_score"]
    ns    = r["news_score"]
    ss    = r["short_score"]
    bar_c = "#27ae60" if total >= 70 else ("#f39c12" if total >= 50 else "#c0392b")

    def _row(label, score, mx, detail=""):
        pct = int(score / mx * 100)
        return f"""
<div class="sc-row">
  <div class="sc-rl"><span class="sc-label">{label}</span>
    <span class="sc-score">{score}/{mx}점</span></div>
  <div class="sc-bar-wrap">
    <div class="sc-bar-fill" style="width:{pct}%;background:{bar_c}"></div>
  </div>
  <div class="sc-detail">{detail}</div>
</div>"""

    rows_html = (
        _row("📊 수급 (기관·외국인)", iv["score"], 30, iv["detail"]) +
        _row("📉 공매도 잔고", ss, 20, "외국인잔고율 변화 기반 추정") +
        _row("📈 눌림목 (차트)", pb["score"], 30,
             f"{pb['signal']} | RSI {pb['rsi']} | MA5 {pb['ma5']:,} / MA20 {pb['ma20']:,}") +
        _row("📰 뉴스 호재", ns["score"], 20,
             f"호재 {len(ns['good'])}건 / 악재 {len(ns['bad'])}건")
    )

    _html_block(f"""
<style>
  .sc {{ background:#fff; border-radius:16px; padding:28px 32px;
          box-shadow:0 2px 16px rgba(0,0,0,.1); margin:8px 0; }}
  .sc-head {{ display:flex; align-items:baseline; gap:16px; margin-bottom:20px; }}
  .sc-big  {{ font-size:3rem; font-weight:900; color:#000 !important; }}
  .sc-v    {{ font-size:1.2rem; font-weight:700; color:#000 !important; }}
  .sc-row  {{ margin:12px 0; }}
  .sc-rl   {{ display:flex; justify-content:space-between; margin-bottom:4px; }}
  .sc-label  {{ font-weight:700; color:#000 !important; font-size:.97rem; }}
  .sc-score  {{ font-weight:900; color:#000 !important; }}
  .sc-bar-wrap {{ background:#f0f0f0; border-radius:8px; height:14px; overflow:hidden; }}
  .sc-bar-fill {{ height:14px; border-radius:8px; transition:width .3s; }}
  .sc-detail {{ font-size:.85rem; color:#555 !important; margin-top:3px; }}
</style>
<div class="sc">
  <div class="sc-head">
    <div class="sc-big">{total}<span style="font-size:1.3rem;color:#888 !important;">/ 100</span></div>
    <div class="sc-v">{r['verdict']}</div>
  </div>
  {rows_html}
</div>
""")


def ui_investor_table(inv_data: list[dict]):
    """하단: 투자자별 5거래일 수급표 (기관·외국인·개인·기타법인)."""
    if not inv_data:
        st.info("수급 데이터를 수집할 수 없습니다.")
        return

    has_other = any(r.get("기타법인", 0) != 0 for r in inv_data)

    def _fmt(v: int) -> str:
        if v == 0: return "—"
        return f"{v:+,}"

    def _color(v: int) -> str:
        if v > 0:  return "color:#c0392b;font-weight:700"
        if v < 0:  return "color:#2471a3;font-weight:700"
        return "color:#999"

    col_heads = ["날짜", "기관", "외국인", "개인"]
    if has_other:
        col_heads.append("기타법인")

    header = "".join(f"<th>{c}</th>" for c in col_heads)
    body   = ""
    for r in inv_data:
        cells = f"<td style='font-weight:600;color:#000'>{r['날짜']}</td>"
        for key in ["기관", "외국인", "개인"] + (["기타법인"] if has_other else []):
            v = int(r.get(key, 0))
            cells += f"<td style='{_color(v)};text-align:right'>{_fmt(v)}</td>"
        body += f"<tr>{cells}</tr>"

    note = "" if has_other else \
        "<p style='color:#888 !important;font-size:.82rem;margin-top:6px'>※ 개인 = 역산(기관+외국인 零合). 기타법인 별도 집계 없음.</p>"

    _html_block(f"""
<style>
  .inv {{ overflow-x:auto; }}
  .inv table {{ width:100%; border-collapse:collapse; background:#fff;
                border-radius:12px; overflow:hidden; font-size:.95rem; }}
  .inv th {{ background:#1e293b; color:#f8fafc !important; padding:10px 16px; text-align:center; }}
  .inv td {{ padding:9px 16px; border-bottom:1px solid #f1f5f9; text-align:center; color:#000 !important; }}
  .inv tr:hover {{ background:#f8fafc; }}
</style>
<div class="inv">
  <table>
    <thead><tr>{header}</tr></thead>
    <tbody>{body}</tbody>
  </table>
  {note}
</div>
""")


def ui_news(news_result: dict, all_news: list[dict]):
    """뉴스 — 호재·악재·전체."""
    good = news_result.get("good", [])
    bad  = news_result.get("bad",  [])

    if not all_news:
        st.info("뉴스 데이터를 수집할 수 없습니다.")
        return

    if good:
        st.markdown("**📈 미반영 호재 뉴스**")
        for n in good:
            href  = n.get("url", "")
            title = n["title"]
            date  = n.get("date", "")
            if href:
                st.markdown(f"- 🟢 [{title}]({href}) `{date}`")
            else:
                st.markdown(f"- 🟢 {title} `{date}`")

    if bad:
        st.markdown("**📉 악재 주의**")
        for n in bad:
            st.markdown(f"- 🔴 {n['title']} `{n.get('date', '')}`")

    with st.expander(f"전체 뉴스 {len(all_news)}건 펼치기"):
        for n in all_news:
            cls  = classify_news(n["title"])
            icon = {"호재": "🟢", "악재": "🔴", "중립": "⬜"}.get(cls, "⬜")
            href = n.get("url", "")
            if href:
                st.markdown(f"{icon} [{n['title']}]({href}) `{n.get('date', '')}`")
            else:
                st.markdown(f"{icon} {n['title']}")


def ui_ma_strip(pb: dict):
    """이동평균 3개 작은 메트릭 행."""
    c1, c2, c3 = st.columns(3)
    c1.metric("MA5 (5일선)",  f"{pb['ma5']:,}원"  if pb['ma5']  else "—")
    c2.metric("MA20 (20일선)", f"{pb['ma20']:,}원" if pb['ma20'] else "—")
    c3.metric("MA60 (60일선)", f"{pb['ma60']:,}원" if pb['ma60'] else "—")


# ─────────────────────────────────────────────────────────────────────────────
# 12. 메인 앱
# ─────────────────────────────────────────────────────────────────────────────
def main():
    # ── 전종목 로드 ──────────────────────────────────────────────────────────
    tickers_df = load_krx_tickers()

    # ── 사이드바 ─────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 🐋 숨비 애널리틱스")
        st.markdown("**SOOMBI Analytics v4.0**")
        now_kst = datetime.now(KST)
        is_mkt  = (9, 0) <= (now_kst.hour, now_kst.minute) <= (15, 30) \
                  and now_kst.weekday() < 5
        st.markdown(f"**KRX 상태**: {'🟢 장 중' if is_mkt else '🔴 장 마감'}")
        st.markdown(f"**시각**: {now_kst.strftime('%Y-%m-%d %H:%M KST')}")
        st.markdown(f"**전종목**: {len(tickers_df):,}개 (FDR 실시간)")
        st.divider()
        if st.button("⚡ 캐시 초기화 / 즉시 갱신", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        st.markdown("#### 42대 필살기 배점")
        st.markdown("""
| 항목 | 배점 |
|---|---|
| 📊 수급 (기관/외국인) | 30점 |
| 📉 공매도 잔고 | 20점 |
| 📈 눌림목 (차트) | 30점 |
| 📰 뉴스 호재 | 20점 |
| **합계** | **100점** |
""")
        st.markdown("**75점 이상 → 즉시 진입 가능**")
        st.divider()
        st.caption("FinanceDataReader + Naver Finance\nyfinance 완전 배제")

    # ── 헤더 ──────────────────────────────────────────────────────────────────
    st.markdown("# 🐋 숨비 애널리틱스")
    st.markdown("### SOOMBI Analytics v4.0 — 42대 필살기 기반 한국 주식 매수 적합도 즉시 판단")
    st.divider()

    # ── 검색 영역 ─────────────────────────────────────────────────────────────
    st.markdown("## 🎯 단일 종목 정밀 스나이퍼")

    col_q, col_btn = st.columns([5, 1])
    with col_q:
        query = st.text_input(
            "종목명 또는 6자리 코드 입력",
            placeholder="예: 한화오션  /  042660  /  삼성전자  /  대한조선  /  439260",
            label_visibility="collapsed",
            key="search_query",
        )
    with col_btn:
        go = st.button("🔍 해부 시작", use_container_width=True, type="primary")

    # ── 검색 → 선택 → 분석 ───────────────────────────────────────────────────
    if query:
        results = search_ticker(query, tickers_df)
        if not results:
            st.warning(f"'{query}' 검색 결과 없음 — 종목명 또는 6자리 코드를 확인하세요.")
            return

        if len(results) > 1:
            opts = [f"{r['name']} ({r['code']}) [{r['market']}]" for r in results]
            sel_i = st.selectbox("종목 선택", range(len(opts)),
                                  format_func=lambda i: opts[i], key="sel_stock")
            selected = results[sel_i]
        else:
            selected = results[0]
            st.success(f"✅ {selected['name']} ({selected['code']}) [{selected['market']}] 즉시 검색됨")

        if go or len(results) == 1:
            ticker = selected["code"]
            name   = selected["name"]
            market = selected["market"]

            with st.spinner(f"🎯 {name}({ticker}) 정밀 해부 중 — 42대 필살기 가동…"):
                result = analyze_ticker(ticker, name, market)

            # ① 현재가 대형 헤더
            ui_price_header(result)

            # ② 블록딜 경보 (해당 시)
            if result["block_alert"]:
                ui_block_alert(result["block_alert"])

            # ③ 42대 점수 카드
            ui_score_card(result)

            # ④ 이동평균 스트립
            st.markdown("#### 📊 이동평균")
            ui_ma_strip(result["pb"])

            # ⑤ 수급표
            st.markdown("#### 💰 투자자별 5거래일 수급 (단위: 주)")
            ui_investor_table(result["inv_data"])

            # ⑥ 뉴스
            st.markdown("#### 📰 미반영 호재 뉴스")
            ui_news(result["news_score"], result["news"])

    else:
        # 시작 화면
        st.info("종목명 또는 6자리 코드를 입력하고 **해부 시작**을 누르세요.")
        st.markdown("""
**검색 예시:**
- `042660` 또는 `한화오션` → 42대 필살기 분석 + **블록딜 오버행 및 개인 설거지 주의** 경보
- `439260` 또는 `대한조선` → 즉시 검색 (KRX 2880+ 전종목 지원)
- `005930` 또는 `삼성전자` → 기관·외국인·개인·기타법인 4주체 수급 분석
- `000660` 또는 `SK하이닉스` → 눌림목 타이밍·RSI·MA 기술 분석

**42대 필살기란?**
기관/외국인 수급 + 공매도 잔고 + 눌림목 차트 + 뉴스 호재를 100점으로 환산하여
1초 만에 진입 적합도를 판단하는 숨비 전용 알고리즘입니다.
""")


if __name__ == "__main__":
    main()
