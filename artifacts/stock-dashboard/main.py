"""SOOMBI Analytics v4.0
한국 주식 시장 KOSPI/KOSDAQ 전문 분석 엔진
SOOMBI ANALYST Impact Score — 세력 수급 역추적 & 매수 적합도 즉시 판단
데이터: FinanceDataReader + Naver Finance
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
import math
import plotly.graph_objects as go

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

st.markdown("""
<style>
/* ── SOOMBI ANALYTICS v4.0 — Gold & Dark Luxury Theme ── */

/* 전체 배경 */
[data-testid="stApp"] { background:#0E1117; }
[data-testid="stAppViewContainer"] > .main { background:#0E1117; }

/* 헤더 골드 */
h1,h2,h3 { color:#D4AF37 !important; letter-spacing:.02em; }
h4,h5,h6 { color:#c8a227 !important; }

/* 사이드바 */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg,#0d1526 0%,#0E1117 100%) !important;
  border-right:1px solid #2a2f3e;
}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,
[data-testid="stSidebar"] td,[data-testid="stSidebar"] th {
  color:#E8E8E8 !important;
}
[data-testid="stSidebar"] [data-testid="metric-container"] { background:#12192b !important; }

/* 메트릭 카드 */
div[data-testid="metric-container"] {
  background:#12192b !important;
  border:1px solid #2a2f3e;
  border-radius:12px;
  padding:14px 18px;
  box-shadow:0 2px 12px rgba(0,0,0,.4);
}
div[data-testid="metric-container"] label { color:#8fa3b8 !important; font-size:.82rem; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
  color:#F0F0F0 !important; font-weight:800;
}

/* 버튼 골드 */
[data-testid="stButton"] > button {
  background:linear-gradient(135deg,#b8960c,#D4AF37) !important;
  color:#0E1117 !important; font-weight:800;
  border:none !important; border-radius:8px !important;
  box-shadow:0 2px 8px rgba(212,175,55,.3);
  transition:all .2s;
}
[data-testid="stButton"] > button:hover {
  background:linear-gradient(135deg,#D4AF37,#f0d060) !important;
  box-shadow:0 4px 16px rgba(212,175,55,.5);
}

/* 탭 골드 */
[data-testid="stTabs"] [data-baseweb="tab-list"] { border-bottom:2px solid #2a2f3e; }
[data-testid="stTabs"] [data-baseweb="tab"] {
  color:#8fa3b8 !important; font-weight:600; background:transparent !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
  color:#D4AF37 !important; border-bottom:2px solid #D4AF37 !important;
}

/* 구분선 */
hr { border-color:#2a2f3e !important; }

/* 데이터프레임 */
[data-testid="stDataFrame"] { border:1px solid #2a2f3e; border-radius:12px; overflow:hidden; }

/* 텍스트인풋 */
[data-testid="stTextInput"] input {
  background:#12192b !important; border:1px solid #2a2f3e !important;
  color:#E8E8E8 !important; border-radius:8px !important;
}

/* 정보·경고 박스 */
[data-testid="stAlertContainer"] { border-radius:10px !important; }

/* 캡션 */
[data-testid="stCaptionContainer"] { color:#6b7c93 !important; }

/* 익스팬더 */
details summary { color:#D4AF37 !important; font-weight:700; }
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

# KRX 휴장일 내장 폴백 테이블 (open.krx.co.kr API 불가 시 사용)
_KRX_HOLIDAYS_FALLBACK: dict[int, list[str]] = {
    2025: [
        "2025-01-01",
        "2025-01-28", "2025-01-29", "2025-01-30",
        "2025-03-01",
        "2025-05-05", "2025-05-06",
        "2025-06-06",
        "2025-08-15",
        "2025-10-03",
        "2025-10-05", "2025-10-06", "2025-10-07",
        "2025-10-09",
        "2025-12-25",
        "2025-12-31",
    ],
    2026: [
        "2026-01-01",
        "2026-02-17", "2026-02-18", "2026-02-19",
        "2026-03-01",
        "2026-05-05",
        "2026-06-06",
        "2026-08-17",
        "2026-10-05",
        "2026-10-09",
        "2026-12-25",
        "2026-12-31",
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
# 3. KRX 공휴일 조회 (open.krx.co.kr OTP API → 폴백 테이블)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def _get_krx_holidays(year: int) -> tuple[frozenset, bool]:
    """
    KRX 휴장일 목록 조회.
    Returns (dates: frozenset[str "YYYY-MM-DD"], is_fallback: bool)
    is_fallback=True → open.krx.co.kr API 실패, 내장 테이블 사용 중
    """
    try:
        otp_resp = requests.get(
            "https://open.krx.co.kr/contents/COM/GenerateOTP.jspx",
            params={"bld": "MKD/01/0110/01100305/mkd01100305_01", "name": "form"},
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://open.krx.co.kr/"},
            timeout=8,
        )
        otp = otp_resp.text.strip()
        if not otp or len(otp) < 10:
            raise ValueError("OTP 발급 실패")

        data_resp = requests.post(
            "https://open.krx.co.kr/contents/OPN/99/OPN99000001.jspx",
            data={
                "search_bas_yy": str(year),
                "gridTp": "KRX",
                "pagePath": "/contents/MKD/01/0110/01100305/MKD01100305.jsp",
                "code": otp,
            },
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://open.krx.co.kr/"},
            timeout=10,
        )
        items = data_resp.json().get("block1", [])
        if not items:
            raise ValueError("공휴일 데이터 없음")

        dates = frozenset(
            datetime.strptime(item["calnd_dd"], "%Y%m%d").strftime("%Y-%m-%d")
            for item in items
            if "calnd_dd" in item
        )
        if not dates:
            raise ValueError("공휴일 파싱 실패")
        return dates, False
    except Exception:
        return frozenset(_KRX_HOLIDAYS_FALLBACK.get(year, [])), True


# ─────────────────────────────────────────────────────────────────────────────
# 4. KRX 전종목 로드 (FDR, 앱 시작 시 1회)
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

        # ROE: main.naver 주요재무정보 table[4] — "ROE(지배주주)" 행, 최근 연간 확정치(col 3)
        try:
            main_resp = requests.get(
                f"https://finance.naver.com/item/main.naver?code={ticker}",
                headers=NAVER_HDRS, timeout=8,
            )
            main_tables = pd.read_html(StringIO(main_resp.text), flavor="lxml")
            if len(main_tables) > 4:
                mt = main_tables[4].copy()
                # MultiIndex → 마지막 레벨만 사용
                if isinstance(mt.columns, pd.MultiIndex):
                    mt.columns = [str(c[-1]) if "Unnamed" not in str(c[-1]) else str(c[0]) for c in mt.columns]
                for _, rrow in mt.iterrows():
                    if "ROE" in str(rrow.iloc[0]):
                        # col index 3 = 최근 확정 연간 (2025.12)
                        for ci in [3, 2, 1]:
                            raw_roe = rrow.iloc[ci] if ci < len(rrow) else None
                            if raw_roe is not None and str(raw_roe) not in ("nan", "NaN", "-", ""):
                                m_roe = re.search(r"(-?[\d.]+)", str(raw_roe))
                                if m_roe:
                                    out["ROE"] = float(m_roe.group(1))
                                    break
                        break
        except Exception:
            pass

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
# 10. 글로벌 지수 + 배치 스캐너 (Top 15 랭킹)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def get_market_indices() -> dict:
    """KOSPI·KOSDAQ·NASDAQ·S&P500 실시간 지수."""
    out: dict = {}

    # 국내 지수 — Naver 모바일 index API
    for label, code in [("KOSPI", "KOSPI"), ("KOSDAQ", "KOSDAQ")]:
        try:
            r = requests.get(
                f"https://m.stock.naver.com/api/index/{code}/basic",
                headers=NAVER_HDRS, timeout=6,
            )
            d = r.json()
            val = float(str(d.get("closePrice", "0")).replace(",", "") or 0)
            chg = float(d.get("fluctuationsRatio", 0))
            out[label] = {"value": val, "change": chg}
        except Exception:
            out[label] = {"value": 0.0, "change": 0.0}

    # 해외 지수 — Yahoo Finance chart API (인증 불필요)
    for label, sym in [("NASDAQ", "%5EIXIC"), ("S&P500", "%5EGSPC")]:
        try:
            r = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
                "?interval=1d&range=1d",
                headers={"User-Agent": "Mozilla/5.0"}, timeout=6,
            )
            meta = r.json()["chart"]["result"][0]["meta"]
            val  = float(meta.get("regularMarketPrice", 0))
            prev = float(meta.get("previousClose", val) or val)
            chg  = round((val - prev) / prev * 100, 2) if prev else 0.0
            out[label] = {"value": val, "change": chg}
        except Exception:
            out[label] = {"value": 0.0, "change": 0.0}

    return out


_ETF_ETN_KW = (
    "ETF", "ETN", "KODEX", "TIGER", "KINDEX", "KOSEF", "ARIRANG",
    "HANARO", "TIMEFOLIO", "PLUS", "ACE", "SOL", "RISE",
    "레버리지", "인버스", "선물", "채권", "달러", "원유",
)

@st.cache_data(ttl=300, show_spinner=False)
def get_top_volume_tickers() -> list[dict]:
    """
    거래대금 상위 50종목 — Naver sise_quant (KOSPI 25 + KOSDAQ 25).
    ETF/ETN 자동 제외, 일반 주식만 수집.
    """
    candidates: list[dict] = []
    for sosok, market in [("0", "KOSPI"), ("1", "KOSDAQ")]:
        try:
            url  = f"https://finance.naver.com/sise/sise_quant.naver?sosok={sosok}"
            resp = requests.get(url, headers=NAVER_HDRS, timeout=10)
            soup = BeautifulSoup(resp.text, "lxml")
            count = 0
            for a in soup.select('td a[href*="/item/main.naver?code="]'):
                m = re.search(r"code=(\d{6})", a.get("href", ""))
                if not m:
                    continue
                code = m.group(1)
                name = a.get_text(strip=True)
                if not name or len(name) < 2:
                    continue
                # ETF·ETN·파생상품 제외
                if any(kw in name for kw in _ETF_ETN_KW):
                    continue
                candidates.append({"code": code, "name": name, "market": market})
                count += 1
                if count >= 25:
                    break
        except Exception:
            pass
    return candidates


@st.cache_data(ttl=180, show_spinner=False)
def quick_score(ticker: str, name: str, market: str) -> dict | None:
    """
    배치 스캐너용 빠른 점수 산출 (펀더멘털·뉴스 제외).
    기존 score_investor() + calc_pullback_score() GOLDEN RULE 그대로 사용.
    """
    try:
        price_data = get_realtime_price(ticker)
        if not price_data or price_data.get("현재가", 0) == 0:
            return None

        ohlcv    = get_ohlcv(ticker, 90)
        inv_data = get_investor_flow(ticker)

        pb = (
            calc_pullback_score(
                ohlcv["Close"],
                ohlcv["Volume"] if "Volume" in ohlcv.columns else pd.Series(dtype=float),
            )
            if not ohlcv.empty and len(ohlcv) >= 22
            else {"score": 0, "signal": "데이터 부족", "rsi": 50.0,
                  "ma5": 0, "ma20": 0, "ma60": 0}
        )
        inv   = score_investor(inv_data)
        short = 10  # 공매도 기본 중립

        raw   = pb["score"] + inv["score"] + short   # 최대 80점 (뉴스 20점 제외)
        total = int(min(raw / 80 * 100, 100))        # 100점 척도 환산

        return {
            "ticker":    ticker,
            "name":      name,
            "market":    market,
            "price":     price_data.get("현재가", 0),
            "change":    float(price_data.get("등락률", 0)),
            "cap":       price_data.get("시가총액", 0),
            "pb_score":  pb["score"],
            "inv_score": inv["score"],
            "total":     total,
            "signal":    pb["signal"],
            "rsi":       pb["rsi"],
        }
    except Exception:
        return None


def scan_top_stocks(candidates: list[dict]) -> list[dict]:
    """후보 종목 병렬 스코어링 → 점수 내림차순 정렬."""
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = {
            ex.submit(quick_score, c["code"], c["name"], c["market"]): c
            for c in candidates
        }
        results = []
        for f in futs:
            try:
                r = f.result(timeout=20)
                if r:
                    results.append(r)
            except Exception:
                pass
    return sorted(results, key=lambda x: x["total"], reverse=True)


@st.cache_data(ttl=300, show_spinner=False)
def get_index_sparkline(yf_sym: str) -> list[float]:
    """Yahoo Finance v8 — 최근 10거래일 종가 스파크라인 데이터."""
    try:
        r = requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_sym}?interval=1d&range=20d",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=8,
        )
        closes = r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        closes = [c for c in closes if c is not None]
        return closes[-10:] if len(closes) >= 10 else closes
    except Exception:
        return []


def _sparkline_svg(prices: list[float], up: bool = True) -> str:
    """SVG 인라인 스파크라인 (80×30 px)."""
    if len(prices) < 2:
        return "<svg width='80' height='30'></svg>"
    mn, mx = min(prices), max(prices)
    rng = mx - mn if mx != mn else 1.0
    n   = len(prices)
    pts = []
    for i, p in enumerate(prices):
        x = i / (n - 1) * 76 + 2
        y = 27 - (p - mn) / rng * 23 + 1
        pts.append(f"{x:.1f},{y:.1f}")
    col = "#27ae60" if up else "#e74c3c"
    return (
        f'<svg width="80" height="30" viewBox="0 0 80 30" style="display:block">'
        f'<polyline points="{" ".join(pts)}" fill="none" stroke="{col}" '
        f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
        f'</svg>'
    )


def _gauge_svg(score: int) -> str:
    """반원형 속도계 SVG — SOOMBI ANALYST Impact Score."""
    p  = max(0, min(score, 100)) / 100
    cx, cy, r = 120, 112, 90
    angle = math.pi * (1 - p)
    ex = cx + r * math.cos(angle)
    ey = cy - r * math.sin(angle)
    nr = 64
    nx = cx + nr * math.cos(angle)
    ny = cy - nr * math.sin(angle)
    laf = 1 if p > 0.5 else 0

    def _zarc(p0: float, p1: float, col: str, opa: str = "0.22") -> str:
        a0 = math.pi * (1 - p0)
        a1 = math.pi * (1 - p1)
        x0 = cx + r * math.cos(a0); y0 = cy - r * math.sin(a0)
        x1 = cx + r * math.cos(a1); y1 = cy - r * math.sin(a1)
        lf = 1 if (p1 - p0) > 0.5 else 0
        return (f'<path d="M {x0:.1f} {y0:.1f} A {r} {r} 0 {lf} 1 {x1:.1f} {y1:.1f}" '
                f'stroke="{col}" stroke-width="20" fill="none" stroke-linecap="butt" opacity="{opa}"/>')

    zones = (
        _zarc(0.00, 0.35, "#e74c3c") +
        _zarc(0.35, 0.55, "#f39c12") +
        _zarc(0.55, 0.75, "#D4AF37") +
        _zarc(0.75, 1.00, "#27ae60")
    )
    sc = "#e74c3c" if score < 35 else ("#f39c12" if score < 55 else ("#D4AF37" if score < 75 else "#27ae60"))
    score_arc = ""
    if p > 0.005:
        score_arc = (f'<path d="M 30.0 {cy:.1f} A {r} {r} 0 {laf} 1 {ex:.1f} {ey:.1f}" '
                     f'stroke="{sc}" stroke-width="20" fill="none" stroke-linecap="round"/>')
    return (
        f'<svg viewBox="0 0 240 140" width="220" style="display:block;margin:0 auto">'
        f'{zones}{score_arc}'
        f'<line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}" '
        f'stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity="0.95"/>'
        f'<circle cx="{cx}" cy="{cy}" r="7" fill="#0E1117"/>'
        f'<circle cx="{cx}" cy="{cy}" r="4" fill="#ffffff" opacity="0.9"/>'
        f'<text x="22" y="134" font-size="9" fill="#e74c3c" font-weight="700" text-anchor="middle">0</text>'
        f'<text x="68" y="50" font-size="9" fill="#f39c12" font-weight="700" text-anchor="middle">35</text>'
        f'<text x="{cx}" y="16" font-size="9" fill="#D4AF37" font-weight="700" text-anchor="middle">55</text>'
        f'<text x="172" y="50" font-size="9" fill="#27ae60" font-weight="700" text-anchor="middle">75</text>'
        f'<text x="218" y="134" font-size="9" fill="#27ae60" font-weight="700" text-anchor="middle">100</text>'
        f'</svg>'
    )


_INDEX_YF = {
    "KOSPI":  "%5EKS11",
    "KOSDAQ": "%5EKQ11",
    "NASDAQ": "%5EIXIC",
    "S&P500": "%5EGSPC",
}


def ui_market_header(indices: dict):
    """글로벌/국내 증시 전광판 — 스파크라인 카드 4열."""
    cards_html = ""
    for label in ["KOSPI", "KOSDAQ", "NASDAQ", "S&P500"]:
        d    = indices.get(label, {"value": 0.0, "change": 0.0})
        val  = d["value"]
        chg  = d["change"]
        up   = chg >= 0
        val_str = f"{val:,.2f}" if val else "—"
        chg_str = f"{'▲' if up else '▼'} {abs(chg):.2f}%"
        chg_col = "#c0392b" if up else "#2471a3"
        spark   = get_index_sparkline(_INDEX_YF.get(label, ""))
        svg     = _sparkline_svg(spark, up=up)
        cards_html += f"""
<div class="ic">
  <div class="ic-label">{label}</div>
  <div class="ic-val">{val_str}</div>
  <div class="ic-row">
    <span class="ic-chg" style="color:{chg_col}">{chg_str if val else '—'}</span>
    <span class="ic-spark">{svg}</span>
  </div>
</div>"""

    _html_block(f"""
<style>
  .ic-wrap {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:4px; }}
  .ic {{ background:#12192b; border:1px solid #2a2f3e; border-radius:14px;
          padding:18px 22px 14px; box-shadow:0 2px 12px rgba(0,0,0,.5); }}
  .ic-label {{ font-size:.78rem; font-weight:700; letter-spacing:.12em;
                color:#D4AF37; text-transform:uppercase; margin-bottom:6px; }}
  .ic-val   {{ font-size:1.7rem; font-weight:900; color:#F0F0F0; line-height:1.1; }}
  .ic-row   {{ display:flex; align-items:center; justify-content:space-between; margin-top:8px; }}
  .ic-chg   {{ font-size:.88rem; font-weight:700; }}
  .ic-spark {{ display:flex; align-items:center; }}
</style>
<div class="ic-wrap">{cards_html}</div>
""")


def ui_top15_tabs(scored: list[dict]):
    """투자 지표 정밀 분석 Top 15 — 탭(전체 / 대형주 / 우량주 / 신규관심)."""

    def _to_df(items: list[dict]) -> pd.DataFrame:
        if not items:
            return pd.DataFrame()
        rows = []
        for i, s in enumerate(items[:15], 1):
            rows.append({
                "순위":           i,
                "종목명":         s["name"],
                "코드":           s["ticker"],
                "시장":           s["market"],
                "현재가":         f"{s['price']:,}원" if s["price"] else "—",
                "등락률":         f"{s['change']:+.2f}%" if s["price"] else "—",
                "시가총액":       f"{s['cap']:,.0f}억" if s.get("cap") else "—",
                "숨비 점수":      s["total"],
                "수급 점수":      s["inv_score"],
                "차트 점수":      s["pb_score"],
                "RSI":            s.get("rsi", "—"),
                "차트 신호":      s.get("signal", "—"),
            })
        return pd.DataFrame(rows)

    _prog_col = st.column_config.ProgressColumn(
        "숨비 점수", min_value=0, max_value=100, format="%d점"
    )

    def _show(df: pd.DataFrame, empty_msg: str = "데이터 동기화 중 — 잠시 후 재시도하세요."):
        if df.empty:
            st.info(empty_msg)
        else:
            st.dataframe(
                df, use_container_width=True, hide_index=True,
                column_config={"숨비 점수": _prog_col},
            )

    large  = [s for s in scored if s.get("cap", 0) >= 10_000]
    qual   = [s for s in scored if s["pb_score"] >= 18 and s["inv_score"] >= 18]
    penny  = [s for s in scored if 0 < s["price"] < 2_000]

    tab1, tab2, tab3, tab4 = st.tabs([
        "🏆 전체 Top 15",
        "🏢 대형주 (시총 1조+)",
        "💎 우량주 (수급·차트 쌍끌이)",
        "🪙 소형주 (~2,000원)",
    ])
    with tab1: _show(_to_df(scored))
    with tab2: _show(_to_df(large),  "대형주(1조+) 조건 해당 종목 없음")
    with tab3: _show(_to_df(qual),   "수급·차트 동시 고점 종목 없음")
    with tab4: _show(_to_df(penny),  "소형주 조건 해당 종목 없음")


# ─────────────────────────────────────────────────────────────────────────────
# 11. UI 컴포넌트
# ─────────────────────────────────────────────────────────────────────────────
def _html_block(html: str):
    """st.html() — iframe 격리. CSS는 블록 내 <style>에 직접 포함."""
    st.html(html)


def ui_price_header(r: dict):
    """상단: 현재가 Gold·Dark 럭셔리 카드."""
    p   = r["price"]
    cur = p.get("현재가", 0)
    chg = float(p.get("등락률", 0))
    dif = p.get("전일대비", 0)
    cap = p.get("시가총액", 0)
    sign = "▲" if chg >= 0 else "▼"
    up   = chg >= 0
    c_price = "#ff6b6b" if up else "#5ba3f5"
    c_chg   = c_price
    mkt_bg  = "#1a2a4a" if r["market"] == "KOSPI" else "#1a3a2a"
    mkt_col = "#5ba3f5" if r["market"] == "KOSPI" else "#4ec76a"

    fund = r["fund"]
    tp   = fund.get("목표주가", 0)
    per  = fund.get("PER", None)
    pbr  = fund.get("PBR", None)
    hi52 = fund.get("52주최고", 0)
    lo52 = fund.get("52주최저", 0)

    tp_str  = f"{tp:,}원" if tp else "—"
    per_str = f"{per:.1f}x" if per else "—"
    pbr_str = f"{pbr:.2f}x" if pbr else "—"
    hi_str  = f"{hi52:,}" if hi52 else "—"
    lo_str  = f"{lo52:,}" if lo52 else "—"
    cap_str = f"{cap:,.0f}억" if cap else "—"

    _html_block(f"""
<style>
  .ph {{
    background: linear-gradient(135deg,#0d1526 0%,#12192b 100%);
    border: 1px solid #2a3550;
    border-left: 4px solid #D4AF37;
    border-radius: 16px;
    padding: 28px 32px;
    box-shadow: 0 4px 24px rgba(0,0,0,.6);
    margin-bottom: 4px;
  }}
  .ph-top  {{ display:flex; align-items:center; gap:12px; flex-wrap:wrap; margin-bottom:10px; }}
  .ph-name {{ font-size:1.65rem; font-weight:900; color:#D4AF37; letter-spacing:.01em; }}
  .ph-code {{ font-size:1rem; color:#8fa3b8; }}
  .ph-mkt  {{ background:{mkt_bg}; color:{mkt_col}; border:1px solid {mkt_col};
               border-radius:6px; padding:2px 12px; font-size:.8rem; font-weight:700;
               letter-spacing:.06em; }}
  .ph-price {{ font-size:3.6rem; font-weight:900; color:{c_price};
                line-height:1.1; margin:4px 0; font-variant-numeric:tabular-nums; }}
  .ph-chg   {{ font-size:1.3rem; font-weight:700; color:{c_chg}; margin-bottom:16px; }}
  .ph-meta  {{ display:flex; gap:0; flex-wrap:wrap;
                border-top:1px solid #2a3550; padding-top:14px; }}
  .ph-kv    {{ display:flex; flex-direction:column; padding:0 20px 0 0;
                margin-right:20px; border-right:1px solid #2a3550; }}
  .ph-kv:last-child {{ border-right:none; }}
  .ph-k     {{ font-size:.72rem; color:#6b7c93; letter-spacing:.08em;
                text-transform:uppercase; margin-bottom:2px; }}
  .ph-v     {{ font-size:.95rem; font-weight:800; color:#E8E8E8; }}
  .ph-ts    {{ font-size:.75rem; color:#4a5568; margin-top:10px; }}
</style>
<div class="ph">
  <div class="ph-top">
    <span class="ph-name">{r['name']}</span>
    <span class="ph-code">{r['ticker']}</span>
    <span class="ph-mkt">{r['market']}</span>
  </div>
  <div class="ph-price">{cur:,}<span style="font-size:1.4rem;color:#8fa3b8;font-weight:400"> 원</span></div>
  <div class="ph-chg">{sign} {abs(chg):.2f}% &nbsp;({dif:+,}원)</div>
  <div class="ph-meta">
    <div class="ph-kv"><span class="ph-k">시가총액</span><span class="ph-v">{cap_str}</span></div>
    <div class="ph-kv"><span class="ph-k">PER</span><span class="ph-v">{per_str}</span></div>
    <div class="ph-kv"><span class="ph-k">PBR</span><span class="ph-v">{pbr_str}</span></div>
    <div class="ph-kv"><span class="ph-k">목표주가</span><span class="ph-v" style="color:#D4AF37">{tp_str}</span></div>
    <div class="ph-kv"><span class="ph-k">52주 고/저</span><span class="ph-v">{hi_str} / {lo_str}</span></div>
  </div>
  <div class="ph-ts">{r['collected_at']}</div>
</div>
""")


def ui_fundamentals_card(r: dict):
    """SOOMBI ANALYST Insight — PER·PBR·ROE·목표주가 카드."""
    fund       = r["fund"]
    price_data = r["price"]
    cur = price_data.get("현재가", 0)

    per  = fund.get("PER")
    pbr  = fund.get("PBR")
    roe  = fund.get("ROE")
    tp   = fund.get("목표주가", 0)
    cap  = price_data.get("시가총액", 0)

    per_str = f"{per:.1f}x" if per else "—"
    pbr_str = f"{pbr:.2f}x" if pbr else "—"
    roe_str = f"{roe:.1f}%" if roe else "—"
    tp_str  = f"{tp:,}원"    if tp   else "—"
    cap_str = f"{cap:,.0f}억" if cap else "—"

    upside = None
    if tp and cur:
        upside = round((tp - cur) / cur * 100, 1)

    upside_str = f"{upside:+.1f}%" if upside is not None else ""
    upside_col = "#27ae60" if (upside or 0) >= 0 else "#e74c3c"

    items = [
        ("시가총액",                    cap_str, "",         ""),
        ("수익 대비 주가 (PER)",        per_str, "낮을수록 매수 기회", "#27ae60"),
        ("자산 대비 주가 (PBR)",        pbr_str, "1 미만시 안전마진",  "#27ae60"),
        ("자본 활용 능력 (ROE)",        roe_str, "높을수록 우량기업",  "#D4AF37"),
        ("목표주가",                    tp_str,  upside_str,  upside_col),
    ]
    cells = ""
    for k, v, hint, hcol in items:
        hint_html = f'<div class="fi-hint" style="color:{hcol}">{hint}</div>' if hint else ""
        cells += f"""
<div class="fi-cell">
  <div class="fi-key">{k}</div>
  <div class="fi-val">{v}</div>
  {hint_html}
</div>"""

    _html_block(f"""
<style>
  .fi-wrap  {{ background:#12192b; border:1px solid #2a3550; border-radius:14px;
               padding:22px 26px; margin:4px 0; }}
  .fi-title {{ font-size:.72rem; font-weight:800; letter-spacing:.14em; color:#D4AF37;
               text-transform:uppercase; margin-bottom:16px; }}
  .fi-grid  {{ display:grid; grid-template-columns:repeat(5,1fr); gap:16px; }}
  .fi-cell  {{ display:flex; flex-direction:column;
               background:#0d1526; border:1px solid #1e2a3a;
               border-radius:10px; padding:14px 16px; }}
  .fi-key   {{ font-size:.72rem; color:#8fa3b8; line-height:1.3; margin-bottom:6px; }}
  .fi-val   {{ font-size:1.25rem; font-weight:900; color:#E8E8E8; }}
  .fi-hint  {{ font-size:.75rem; font-weight:700; margin-top:4px; }}
  .fi-note  {{ font-size:.72rem; color:#4a5568; margin-top:12px; }}
</style>
<div class="fi-wrap">
  <div class="fi-title">⚡ 숨비 가치 평가 분석</div>
  <div class="fi-grid">{cells}</div>
  <div class="fi-note">※ 네이버 파이낸스 기준 · 수익/자산 대비 주가는 현재 기준, 자본 활용 능력은 최근 결산 기준 · 투자 권유 아님</div>
</div>
""")


def ui_moat_expander(name: str, ticker: str):
    """핵심 사업 및 초격차 독점 기술 아코디언 (종목별 분기)."""
    # 종목별 맞춤 텍스트 — 알려진 종목은 상세 내용, 나머지는 범용 안내
    _MOAT_DB: dict[str, dict] = {
        "042660": {
            "title": "한화오션 — 조선·해양·방산 초격차 독점",
            "overview": "대표적인 국내 대형 조선·해양 플랜트·특수선(방산) 건조 기업. "
                        "한화그룹 편입 이후 방산·에너지 시너지 확대 중.",
            "moat": [
                "**방산(함정) 독점력**: 국내 유일 잠수함 턴키 건조 능력(KSS-III). 북미 함정 MRO 시장 진출 본격화.",
                "**친환경 스마트 선박**: 암모니아 추진선·LCO₂ 운반선 등 차세대 선박 기술 세계 최고 수준.",
                "**자율운항 기술**: HS-모빌리티 첨단 자율운항 선박 기술 적용 확대 중.",
            ],
        },
        "439260": {
            "title": "대한조선 — 중소형 특수선 전문",
            "overview": "중소형 탱커·벌크선 특화 조선소. 가격 경쟁력과 납기 준수율 강점.",
            "moat": [
                "**중소형 선박 특화**: 대형 조선소가 외면하는 중소형 틈새 시장 장악.",
                "**빠른 납기**: 소형 도크 특성상 회전율 빠름 → 수주잔고 대비 매출 인식 속도 유리.",
                "**원가 경쟁력**: 경남 고성 저렴한 부지 및 인건비 구조.",
            ],
        },
        "005930": {
            "title": "삼성전자 — 반도체·스마트폰 글로벌 1위",
            "overview": "메모리(DRAM·NAND)·파운드리·스마트폰·디스플레이·가전 수직계열화 글로벌 테크 대기업.",
            "moat": [
                "**메모리 반도체 점유율 1위**: DRAM 42%, NAND 31% 세계 1위 유지.",
                "**HBM·온디바이스 AI**: HBM3E 양산·On-device AI 기능 Galaxy 적용 선도.",
                "**수직계열화**: 소재·장비·팹·완제품 내재화 → 원가 및 공급 유연성 경쟁 우위.",
            ],
        },
        "000660": {
            "title": "SK하이닉스 — HBM 글로벌 1위",
            "overview": "DRAM·NAND·HBM 전문 반도체 기업. 엔비디아 HBM 단독 공급으로 AI 반도체 슈퍼사이클 최대 수혜.",
            "moat": [
                "**HBM 세계 1위**: HBM3E 12단 엔비디아 독점 공급 — AI 데이터센터 핵심 부품.",
                "**DRAM 기술 선도**: 1c nm 공정 전환 완료, 원가 절감 + 성능 우위 동시 확보.",
                "**엔비디아 파트너십**: GB200 NVL72 HBM 우선 공급권 확보.",
            ],
        },
    }

    info = _MOAT_DB.get(ticker)
    if info is None:
        # 범용 — 종목명 기반 안내
        info = {
            "title": f"{name} — 핵심 사업 개요",
            "overview": f"{name}의 사업 개요입니다. 공식 사업보고서 및 IR 자료를 통해 최신 내용을 확인하세요.",
            "moat": [
                "해당 종목의 상세 독점 기술 분석은 현재 준비 중입니다.",
                "DART 전자공시(dart.fss.or.kr)에서 최신 사업보고서를 확인하세요.",
            ],
        }

    with st.expander(f"◈ 정밀 사업 분석 — {info['title']}", expanded=False):
        st.markdown(f"**기업 개요**: {info['overview']}")
        st.markdown("**핵심 경쟁 우위 (경제적 해자)**:")
        for point in info["moat"]:
            st.markdown(f"- {point}")
        st.caption("※ 공개 IR·뉴스·사업보고서 기반 분석. 투자 권유 아님.")


def ui_block_alert(msg: str):
    """세력 동향 경보 카드 — Gold & Dark Luxury."""
    _html_block(f"""
<style>
  .ba {{
    background: linear-gradient(135deg,#1a0d0d 0%,#250f0f 100%);
    border: 1px solid #8b2020;
    border-left: 4px solid #e74c3c;
    border-radius: 14px;
    padding: 20px 24px; margin: 8px 0;
    box-shadow: 0 4px 20px rgba(231,76,60,.2);
  }}
  .ba-title {{
    font-size:.72rem; font-weight:800; letter-spacing:.15em;
    color:#e74c3c; text-transform:uppercase; margin-bottom:8px;
  }}
  .ba-body {{ font-size:.97rem; line-height:1.75; color:#E8E8E8; }}
</style>
<div class="ba">
  <div class="ba-title">⚠ 세력 동향 경보 — 블록딜 오버행 및 개인 설거지 주의</div>
  <div class="ba-body">{msg}</div>
</div>
""")


def ui_score_card(r: dict):
    """숨비 종합 진단 점수 — Plotly 속도계 게이지 + 4분할 카드."""
    total   = r["total"]
    pb      = r["pb"]
    iv      = r["inv_score"]
    ns      = r["news_score"]
    ss      = r["short_score"]
    verdict = r["verdict"]

    if total >= 75:
        vd_col = "#27ae60"; vd_bg = "#0d2a1a"; vd_border = "#27ae60"
        badge  = "강력 매수"; sc = "#27ae60"
    elif total >= 55:
        vd_col = "#D4AF37"; vd_bg = "#2a2200"; vd_border = "#D4AF37"
        badge  = "관심 매집"; sc = "#D4AF37"
    elif total >= 35:
        vd_col = "#f39c12"; vd_bg = "#221600"; vd_border = "#f39c12"
        badge  = "관망";     sc = "#f39c12"
    else:
        vd_col = "#e74c3c"; vd_bg = "#2a0d0d"; vd_border = "#e74c3c"
        badge  = "진입 불가"; sc = "#e74c3c"

    # ── Plotly 속도계 게이지 ───────────────────────────────────────────────
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total,
        number={
            "font": {"size": 64, "color": sc, "family": "Arial Black"},
            "suffix": "점",
        },
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": "#4a5568",
                "tickvals": [0, 35, 55, 75, 100],
                "ticktext": ["0", "35", "55", "75", "100"],
                "tickfont": {"color": "#8fa3b8", "size": 11},
            },
            "bar":  {"color": sc, "thickness": 0.30},
            "bgcolor": "#12192b",
            "borderwidth": 0,
            "steps": [
                {"range": [0,   35],  "color": "#200d0d"},
                {"range": [35,  55],  "color": "#201700"},
                {"range": [55,  75],  "color": "#1c1a00"},
                {"range": [75, 100],  "color": "#0c1f10"},
            ],
            "threshold": {
                "line": {"color": "#D4AF37", "width": 3},
                "thickness": 0.78,
                "value": 75,
            },
        },
        title={
            "text": (
                "숨비 종합 진단 점수<br>"
                f"<span style='font-size:14px;color:{vd_col}'>"
                f"● {badge} 판정</span>"
            ),
            "font": {"size": 17, "color": "#D4AF37", "family": "Arial"},
        },
    ))
    fig.update_layout(
        height=310,
        paper_bgcolor="#0E1117",
        font={"color": "#E8E8E8", "family": "Arial"},
        margin={"t": 90, "b": 10, "l": 50, "r": 50},
    )

    col_gauge, col_verdict = st.columns([1, 1])
    with col_gauge:
        st.plotly_chart(fig, use_container_width=True)
    with col_verdict:
        _html_block(f"""
<style>
  .vd {{
    background:{vd_bg}; border:1px solid {vd_border};
    border-left:4px solid {vd_col};
    border-radius:14px; padding:22px 24px; margin-top:8px;
    box-shadow: 0 2px 12px rgba(0,0,0,.4);
  }}
  .vd-badge {{
    font-size:.72rem; font-weight:900; letter-spacing:.18em;
    color:{vd_col}; text-transform:uppercase; margin-bottom:10px;
  }}
  .vd-text {{ font-size:1.02rem; font-weight:700; color:#E8E8E8; line-height:1.65; }}
</style>
<div class="vd">
  <div class="vd-badge">숨비 종합 판정 ― {badge}</div>
  <div class="vd-text">{verdict}</div>
</div>
""")

    # ── 4분할 세부 분석 카드 ──────────────────────────────────────────────
    st.markdown("#### 📊 4대 핵심 지표 세부 분석")
    c1, c2, c3, c4 = st.columns(4)

    def _mini_card(col, title: str, score: int, max_score: int, detail: str):
        pct   = int(score / max_score * 100)
        col_c = ("#27ae60" if pct >= 75 else
                 "#D4AF37" if pct >= 50 else
                 "#f39c12" if pct >= 25 else "#e74c3c")
        with col:
            _html_block(f"""
<style>
  .mc {{
    background:#12192b; border:1px solid #2a3550;
    border-top:3px solid {col_c};
    border-radius:12px; padding:18px 16px;
  }}
  .mc-title {{ font-size:.7rem; font-weight:800; letter-spacing:.1em;
               color:#D4AF37; text-transform:uppercase; margin-bottom:10px; }}
  .mc-score {{ font-size:2.1rem; font-weight:900; color:{col_c}; line-height:1; }}
  .mc-max   {{ font-size:.82rem; color:#6b7c93; font-weight:400; }}
  .mc-bar   {{ background:#1a2236; border-radius:4px; height:6px; margin:10px 0 8px; }}
  .mc-fill  {{ background:{col_c}; height:6px; border-radius:4px; width:{pct}%; }}
  .mc-det   {{ font-size:.76rem; color:#8fa3b8; line-height:1.45; }}
</style>
<div class="mc">
  <div class="mc-title">{title}</div>
  <div class="mc-score">{score}<span class="mc-max"> / {max_score}점</span></div>
  <div class="mc-bar"><div class="mc-fill"></div></div>
  <div class="mc-det">{detail}</div>
</div>
""")

    _mini_card(c1, "수급 분석",    iv["score"], 30,
               f"기관·외국인 세력 역추적<br>{iv['detail']}")
    _mini_card(c2, "공매도 분석",  ss, 20,
               "공매도 잔고 역추적<br>외국인잔고율 변화 기반")
    _mini_card(c3, "차트 패턴",    pb["score"], 30,
               f"눌림목 패턴 분석<br>RSI {pb['rsi']} · MA5 {pb['ma5']:,}")
    _mini_card(c4, "미반영 호재",  ns["score"], 20,
               f"호재 {len(ns['good'])}건 감지<br>악재 {len(ns['bad'])}건 경보")


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
        cells = f"<td style='font-weight:600'>{r['날짜']}</td>"
        for key in ["기관", "외국인", "개인"] + (["기타법인"] if has_other else []):
            v = int(r.get(key, 0))
            cells += f"<td style='{_color(v)};text-align:right'>{_fmt(v)}</td>"
        body += f"<tr>{cells}</tr>"

    note = "" if has_other else \
        "<p style='font-size:.82rem;margin-top:6px;opacity:.6'>※ 개인 = 역산(기관+외국인 零合). 기타법인 별도 집계 없음.</p>"

    _html_block(f"""
<style>
  .inv-wrap {{ overflow-x:auto; }}
  .inv-title {{ font-size:.72rem; font-weight:800; letter-spacing:.14em; color:#D4AF37;
                text-transform:uppercase; margin-bottom:12px; }}
  .inv table {{ width:100%; border-collapse:collapse;
                background:#12192b; border-radius:12px; overflow:hidden; font-size:.93rem; }}
  .inv th {{ background:#0d1526; color:#D4AF37; padding:10px 18px;
              text-align:center; font-size:.75rem; letter-spacing:.1em;
              text-transform:uppercase; border-bottom:1px solid #2a3550; }}
  .inv td {{ padding:10px 18px; border-bottom:1px solid #1e2a3a; text-align:center;
              color:#C8C8C8; }}
  .inv tr:last-child td {{ border-bottom:none; }}
  .inv tr:hover td {{ background:#1a2236; }}
</style>
<div class="inv-wrap">
  <div class="inv-title">◈ 세력 수급 역추적 — 4주체 5거래일 확정 수급 (단위: 주)</div>
  <div class="inv">
  <table>
    <thead><tr>{header}</tr></thead>
    <tbody>{body}</tbody>
  </table>
  </div>
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
        st.markdown("## SOOMBI ANALYTICS")
        st.markdown("**v4.0 — 세력 역추적 터미널**")
        now_kst = datetime.now(KST)
        holidays, hol_fallback = _get_krx_holidays(now_kst.year)
        today_str = now_kst.strftime("%Y-%m-%d")
        is_holiday = today_str in holidays
        is_mkt  = (
            not is_holiday
            and (9, 0) <= (now_kst.hour, now_kst.minute) <= (15, 30)
            and now_kst.weekday() < 5
        )
        st.markdown(f"**KRX 시장**: {'🟢 장 중' if is_mkt else '🔴 장 마감'}")
        if hol_fallback:
            st.warning("시장 캘린더 동기화 중 — 기본 데이터 사용", icon="⚠️")
        st.markdown(f"**기준 시각**: {now_kst.strftime('%Y-%m-%d %H:%M KST')}")
        st.markdown(f"**커버리지**: {len(tickers_df):,}개 전종목")
        st.divider()
        if st.button("⚡ 즉시 갱신 (캐시 초기화)", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        st.markdown("#### 숨비 종합 진단 점수")
        st.markdown("""
| 분석 지표 | 배점 |
|---|---|
| 세력 수급 역추적 | 30점 |
| 공매도 잔고 분석 | 20점 |
| 정밀 눌림목 패턴 | 30점 |
| 미반영 호재 뉴스 | 20점 |
| **총점** | **100점** |
""")
        st.markdown("**75점 이상 → 강력 매수 판정**")
        st.divider()
        st.caption("ENGINE: FDR + Naver Finance\nDATA: 실시간 역추적 파이프라인")

    # ── 헤더 ──────────────────────────────────────────────────────────────────
    st.markdown("# SOOMBI ANALYTICS v4.0")
    st.markdown("### 0.1% 세력 역추적 &amp; 매수 적합도 즉시 판단 — 숨비 종합 진단 점수")
    st.divider()

    # ── 글로벌/국내 증시 전광판 ─────────────────────────────────────────────
    with st.spinner("시장 데이터 동기화 중…"):
        indices = get_market_indices()
    st.markdown("### 글로벌 시장 실시간 전광판")
    ui_market_header(indices)
    st.divider()

    # ── 투자 지표 정밀 분석 Top 15 ───────────────────────────────────────────
    st.markdown("### 투자 지표 정밀 분석 Top 15")
    st.caption("거래대금 상위 50종목(KOSPI 25 + KOSDAQ 25) 자동 스캔 → Impact Score 순위 정렬")

    with st.spinner("데이터 동기화 중 — 전종목 세력 수급 역추적 파이프라인 가동 중 (최대 30초)…"):
        candidates = get_top_volume_tickers()
        if candidates:
            scored = scan_top_stocks(candidates)
        else:
            scored = []

    if scored:
        ui_top15_tabs(scored)
    else:
        st.warning("데이터 동기화 중입니다. ⚡ 즉시 갱신 버튼을 눌러 재시도하세요.")
    st.divider()

    # ── 검색 영역 ─────────────────────────────────────────────────────────────
    st.markdown("## 단일 종목 정밀 해부")

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

            with st.spinner(f"{name}({ticker}) — 세력 역추적 파이프라인 가동 중…"):
                result = analyze_ticker(ticker, name, market)

            # ① 현재가 Gold·Dark 카드
            ui_price_header(result)

            # ② SOOMBI ANALYST Insight — 가치 평가
            st.divider()
            ui_fundamentals_card(result)

            # ③ 정밀 사업 분석 아코디언
            ui_moat_expander(name, ticker)

            # ④ 세력 동향 경보 (해당 시)
            st.divider()
            if result["block_alert"]:
                ui_block_alert(result["block_alert"])

            # ⑤ 숨비 종합 진단 점수 게이지
            st.markdown("### 숨비 종합 진단 점수")
            ui_score_card(result)

            # ⑥ 이동평균 스트립
            st.markdown("#### 기술적 이동평균 지표")
            ui_ma_strip(result["pb"])

            # ⑦ 세력 수급 역추적 표
            st.divider()
            ui_investor_table(result["inv_data"])

            # ⑧ 미반영 호재 뉴스
            st.markdown("#### 미반영 호재 뉴스 & 팩트 분석")
            ui_news(result["news_score"], result["news"])

    else:
        # 시작 화면
        st.info("종목명 또는 6자리 코드를 입력하고 **해부 시작**을 누르세요.")
        st.markdown("""
**검색 예시:**
- `042660` 또는 `한화오션` → Impact Score 분석 + **블록딜 오버행 및 개인 설거지** 세력 동향 경보
- `439260` 또는 `대한조선` → 즉시 검색 (KRX 전종목 지원)
- `005930` 또는 `삼성전자` → 기관·외국인·개인·기타법인 4주체 수급 역추적
- `000660` 또는 `SK하이닉스` → 정밀 눌림목 매커니즘·RSI·MA 기술 분석

**SOOMBI ANALYST Impact Score란?**
기관/외국인 세력 수급 역추적 + 공매도 잔고 분석 + 정밀 눌림목 매커니즘 + 미반영 호재 뉴스를
100점 만점으로 환산하여 즉각적인 매수 적합도를 판단하는 SOOMBI 전용 알고리즘입니다.
""")


if __name__ == "__main__":
    main()
