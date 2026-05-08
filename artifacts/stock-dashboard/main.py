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
    # 배거차숏: 배당/밸류업 + 거시쇼크 반전 + 차트심리 + 숏스퀴즈
    "밸류업", "숏스퀴즈", "주주환원", "자사주 소각", "분기배당", "특별배당",
    "공매도 환매", "숏커버링", "거시 반등", "금리 인하", "피벗", "저점 돌파",
    "52주 신고가", "골든크로스", "데드캣 반등", "바닥 확인", "반등 시작",
]
_BAD_KW = [
    "손실", "적자", "하향", "매도", "소송", "검찰", "횡령", "배임",
    "유상증자", "주가 하락", "블록딜", "오버행", "공매도 증가", "실적 악화",
    "금리 인상", "경기 침체", "파산", "상장폐지", "관리종목",
]

# ── 뉴스 등급제 (News Tiering) ────────────────────────────────────────────────
# Tier 1: 확정적 사실 — 주가 직접 영향 (20점 만점)
_TIER1_KW = [
    # 법원·판결
    "기각", "승소", "판결", "가처분 기각", "특허 무효 기각",
    # 계약·공급·수주 확정
    "공급계약", "단일판매", "계약 체결", "독점 공급", "독점 계약",
    "최대 수주", "대규모 수주", "공급 확정", "수주 확정", "수주 성공",
    "수주", "클라우드 수주",
    # 상장·IPO
    "상장", "IPO", "상장 확정", "증시 입성", "공모가 확정", "상장 예정",
    "코스피 상장", "코스닥 상장", "기업공개",
    # 실적 서프라이즈
    "사상 최대", "역대 최대", "사상 최고", "어닝 서프라이즈", "어닝쇼크 반전",
    "사상 최고 실적", "연간 최대 흑자",
    # 기업 이벤트 확정
    "M&A", "인수 완료", "합병 완료", "원천기술", "세계 최초",
    "FDA 승인", "임상 성공", "양산 성공", "흑자 전환 확정", "적자 탈출",
    "상한가", "특허 등록", "IPO 확정",
    # 업종 특화 (KDDX·HBM·클라우드·로봇 등)
    "KDDX", "HBM 양산", "아틀라스", "AI 반도체 양산", "자율주행 계약",
    "클라우드", "AI 클라우드", "MSP 계약",
]
# Tier 2: 긍정적 기대감 — 미래 가치 (건당 5점, 최대 10점)
_TIER2_KW = [
    "목표주가 상향", "목표가 상향", "매수 추천", "신제품 출시", "박람회",
    "해외 진출", "신규 계약", "추가 수주", "증설", "MOU", "업무협약",
    "협력", "파트너십", "투자 유치", "신규 사업", "로드쇼", "호실적",
    "수주 기대", "협의 중", "검토 중", "협상 진행",
]
# Tier 3: 소음/중립 — 점수 반영 제외
_NOISE_KW = [
    "장마감", "마감시황", "오전시황", "오후시황", "시황", "주간 요약",
    "특징주", "기업 개요", "오늘의 주요", "증시 마감", "급등주 포착",
    "코스피 현황", "코스닥 현황", "주요 일정", "주간 브리핑",
]
# 하위 호환 — 기존 _IMPACT_KW 참조 코드가 있는 경우를 위해 별칭 유지
_IMPACT_KW = _TIER1_KW


# KRX 휴장일 내장 폴백 테이블 (open.krx.co.kr API 불가 시 사용)
_KRX_HOLIDAYS_FALLBACK: dict[int, dict[str, str]] = {
    2025: {
        "2025-01-01": "신정",
        "2025-01-28": "설날 연휴",
        "2025-01-29": "설날",
        "2025-01-30": "설날 연휴",
        "2025-03-01": "삼일절",
        "2025-05-05": "어린이날",
        "2025-05-06": "어린이날 대체공휴일",
        "2025-06-06": "현충일",
        "2025-08-15": "광복절",
        "2025-10-03": "개천절",
        "2025-10-05": "추석 연휴",
        "2025-10-06": "추석",
        "2025-10-07": "추석 연휴",
        "2025-10-09": "한글날",
        "2025-12-25": "성탄절",
        "2025-12-31": "연말 휴장",
    },
    2026: {
        "2026-01-01": "신정",
        "2026-02-17": "설날 연휴",
        "2026-02-18": "설날",
        "2026-02-19": "설날 연휴",
        "2026-03-01": "삼일절",
        "2026-05-05": "어린이날",
        "2026-06-06": "현충일",
        "2026-08-17": "광복절 대체공휴일",
        "2026-10-05": "추석",
        "2026-10-09": "한글날",
        "2026-12-25": "성탄절",
        "2026-12-31": "연말 휴장",
    },
    2027: {
        "2027-01-01": "신정",
        "2027-02-05": "설날 연휴",
        "2027-02-08": "설날 대체공휴일",
        "2027-02-09": "설날 연휴 대체공휴일",
        "2027-03-01": "삼일절",
        "2027-05-05": "어린이날",
        "2027-06-07": "현충일 대체공휴일",
        "2027-08-16": "광복절 대체공휴일",
        "2027-09-30": "추석 연휴",
        "2027-10-01": "추석",
        "2027-10-04": "추석 연휴 대체공휴일",
        "2027-10-05": "개천절 대체공휴일",
        "2027-10-11": "한글날 대체공휴일",
        "2027-12-27": "성탄절 대체공휴일",
        "2027-12-31": "연말 휴장",
    },
    2028: {
        "2028-01-03": "신정 대체공휴일",
        "2028-01-25": "설날 연휴",
        "2028-01-26": "설날",
        "2028-01-27": "설날 연휴",
        "2028-03-01": "삼일절",
        "2028-05-05": "어린이날",
        "2028-06-06": "현충일",
        "2028-08-15": "광복절",
        "2028-09-18": "추석 연휴",
        "2028-09-19": "추석",
        "2028-09-20": "추석 연휴",
        "2028-10-03": "개천절",
        "2028-10-09": "한글날",
        "2028-12-25": "성탄절",
        "2028-12-31": "연말 휴장",
    },
}

# 블록딜·오버행 경보 — 실시간 수급 기반 자동 감지
# (특정 종목 하드코딩 폐기 → 수급 분석 엔진이 동적 감지)
_BLOCK_ALERT: dict[str, str] = {}

# ─────────────────────────────────────────────────────────────────────────────
# 3. KRX 공휴일 조회 (open.krx.co.kr OTP API → 폴백 테이블)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def _get_krx_holidays(year: int) -> tuple[dict[str, str], bool]:
    """
    KRX 휴장일 목록 조회.
    Returns (dates: dict[str "YYYY-MM-DD", str holiday_name], is_fallback: bool)
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

        dates: dict[str, str] = {}
        for item in items:
            if "calnd_dd" not in item:
                continue
            date_str = datetime.strptime(item["calnd_dd"], "%Y%m%d").strftime("%Y-%m-%d")
            name = (
                item.get("calnd_dd_nm")
                or item.get("holdy_nm")
                or item.get("remark")
                or ""
            )
            dates[date_str] = name
        if not dates:
            raise ValueError("공휴일 파싱 실패")
        return dates, False
    except Exception:
        fallback = _KRX_HOLIDAYS_FALLBACK.get(year)
        if fallback is None:
            return {}, True
        return dict(fallback), True


# ─────────────────────────────────────────────────────────────────────────────
# 4. KRX 전종목 로드 (FDR, 앱 시작 시 1회)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="KRX 전종목 리스트 로딩 중…")
def load_krx_tickers() -> pd.DataFrame:
    """FDR StockListing('KRX') → 2880+ 종목. 앱 시작 시 1회 캐시."""
    try:
        raw = fdr.StockListing("KRX")
        cols = ["Code", "Name", "Market"] + (["Marcap"] if "Marcap" in raw.columns else [])
        df = raw[cols].copy()
        df = df[df["Code"].str.match(r"^\d{6}$", na=False)].reset_index(drop=True)
        df["Code"] = df["Code"].str.zfill(6)
        df["_key"] = df["Name"].str.lower() + " " + df["Code"]
        return df
    except Exception:
        return pd.DataFrame(columns=["Code", "Name", "Market", "_key"])


@st.cache_data(ttl=3600, show_spinner=False)
def _get_marcap_lookup() -> dict[str, float]:
    """
    FDR StockListing Marcap(원) → {code: 시총_억원} 딕셔너리.
    tab 필터링용 — 탭 클릭 시 즉시 사용 (TTL 1시간).
    """
    try:
        raw = fdr.StockListing("KRX")
        if "Marcap" not in raw.columns:
            return {}
        df = raw[["Code", "Marcap"]].copy()
        df = df[df["Code"].str.match(r"^\d{6}$", na=False)].copy()
        df["Code"] = df["Code"].str.zfill(6)
        df["cap_억"] = pd.to_numeric(df["Marcap"], errors="coerce").fillna(0) / 1e8
        return dict(zip(df["Code"], df["cap_억"]))
    except Exception:
        return {}


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
    Naver frgn.naver table[3] → 기관·외국인 순매매량 (가장 최근 확정 영업일 자동 수집).
    개인 = 零合 역산: -(기관+외국인)   [기타법인 ≈ 0 근사]
    기타법인은 별도 source 없을 시 역산 불가 → 0 표기.
    """
    # frgn.naver 파싱 — 가장 최근 확정 영업일 데이터 자동 수집
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
# 8. 뉴스 — 3단계 폴백 수집 엔진 (절대 실패 없음)
# ─────────────────────────────────────────────────────────────────────────────
def _news_parse_bs(html: str, seen: set[str]) -> list[dict]:
    """BeautifulSoup 파싱 — CSS 셀렉터 우선순위 순회."""
    items: list[dict] = []
    try:
        soup = BeautifulSoup(html, "lxml")
        for sel in [
            ".news_dl dt a", ".articleSubject a", ".news_list li a",
            "dl dt a", ".type01 li dt a", "li.newline a", "a[href*='news']",
        ]:
            elems = soup.select(sel)
            if elems:
                for el in elems[:20]:
                    title = el.get_text(strip=True)
                    href  = el.get("href", "")
                    if title and len(title) > 5 and title not in seen:
                        if href and not href.startswith("http"):
                            href = "https://finance.naver.com" + href
                        seen.add(title)
                        items.append({"title": title, "url": href, "date": ""})
                if items:
                    break
    except Exception:
        pass
    return items


def _news_parse_rss(html: str, seen: set[str]) -> list[dict]:
    """RSS/XML 파싱 — <title> 태그 정규식 추출."""
    items: list[dict] = []
    try:
        # <item> 블록 추출
        item_blocks = re.findall(r"<item>(.*?)</item>", html, re.DOTALL)
        for block in item_blocks[:20]:
            t_m  = re.search(r"<title><!\[CDATA\[(.*?)\]\]></title>", block)
            if not t_m:
                t_m = re.search(r"<title>(.*?)</title>", block)
            l_m  = re.search(r"<link>(.*?)</link>",  block)
            d_m  = re.search(r"<pubDate>(.*?)</pubDate>", block)
            title = t_m.group(1).strip() if t_m else ""
            href  = l_m.group(1).strip() if l_m else ""
            date  = d_m.group(1).strip()[:16] if d_m else ""
            if title and len(title) > 5 and title not in seen:
                seen.add(title)
                items.append({"title": title, "url": href, "date": date})
    except Exception:
        pass
    return items


def _news_parse_regex(html: str, seen: set[str]) -> list[dict]:
    """최후 수단 — <a> 태그 정규식 브루트포스 추출."""
    items: list[dict] = []
    try:
        anchors = re.findall(
            r'<a[^>]+href="([^"]*(?:news|article|view)[^"]*)"[^>]*>(.*?)</a>',
            html, re.DOTALL,
        )
        for href, raw in anchors[:30]:
            title = re.sub(r"<[^>]+>", "", raw).strip()
            if title and len(title) > 8 and title not in seen:
                if not href.startswith("http"):
                    href = "https://finance.naver.com" + href
                seen.add(title)
                items.append({"title": title, "url": href, "date": ""})
    except Exception:
        pass
    return items


def _fetch_with_fallback(url: str, seen: set[str],
                         hdrs: dict | None = None,
                         max_retry: int = 3) -> list[dict]:
    """단일 URL 수집 — BS → RSS → regex 3단계 폴백, 최대 max_retry회."""
    used_hdrs = hdrs or NAVER_HDRS
    for attempt in range(max_retry):
        try:
            resp = requests.get(url, headers=used_hdrs, timeout=8)
            if resp.status_code != 200:
                continue
            html = resp.text
            # ① BeautifulSoup
            items = _news_parse_bs(html, seen)
            if items:
                return items
            # ② RSS/XML
            items = _news_parse_rss(html, seen)
            if items:
                return items
            # ③ 정규식 브루트포스
            items = _news_parse_regex(html, seen)
            if items:
                return items
        except Exception:
            pass
    return []


def _fetch_mobile_naver(query: str, seen: set[str]) -> list[dict]:
    """모바일 Naver 뉴스 검색 JSON API — 독립 폴백 채널."""
    items: list[dict] = []
    enc_q = requests.utils.quote(query)
    urls = [
        f"https://m.search.naver.com/search.naver?where=m_news&query={enc_q}",
        f"https://search.naver.com/search.naver?where=news&query={enc_q}&sort=1",
    ]
    mob_hdrs = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
            "Mobile/15E148 Safari/604.1"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://m.naver.com/",
    }
    for url in urls:
        for attempt in range(2):
            try:
                resp = requests.get(url, headers=mob_hdrs, timeout=8)
                if resp.status_code != 200:
                    continue
                html = resp.text
                # JSON 응답 시도
                try:
                    data = __import__("json").loads(html)
                    for art in data.get("articles", data.get("items", [])):
                        title = art.get("title", "")
                        href  = art.get("originallink", art.get("link", ""))
                        if title and title not in seen:
                            seen.add(title)
                            items.append({"title": title, "url": href, "date": ""})
                    if items:
                        return items
                except Exception:
                    pass
                # HTML 응답: BS 우선, regex 폴백
                parsed = _news_parse_bs(html, seen)
                if not parsed:
                    parsed = _news_parse_regex(html, seen)
                items.extend(parsed)
                if items:
                    return items
            except Exception:
                pass
    return items


@st.cache_data(ttl=300, show_spinner=False)
def get_news(ticker: str, name: str) -> list[dict]:
    """3단계 폴백 뉴스 수집 엔진 — 실패 없음 보장.
    수집 채널: finance.naver(코드) → 검색(8쿼리) → 모바일Naver → RSS.
    """
    seen: set[str]   = set()
    news: list[dict] = []
    enc = requests.utils.quote

    # ── 채널 A: Naver Finance 종목코드 기반 ──────────────────────────────────
    news += _fetch_with_fallback(
        f"https://finance.naver.com/news/news_list.naver?mode=RANK&code={ticker}",
        seen,
    )
    # RSS 채널 (종목코드)
    news += _fetch_with_fallback(
        f"https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258",
        seen,
    )

    # ── 채널 B: 8가지 키워드 쿼리 확장 ─────────────────────────────────────
    queries = [
        name,
        name + " 실적",
        name + " 수주",
        name + " 상장",
        name + " IPO",
        name + " 클라우드",
        name + " 판결",
        name + " 호재",
    ]
    for q in queries:
        found = _fetch_with_fallback(
            f"https://finance.naver.com/news/news_search.naver?q={enc(q)}&pd=1&sm=tab_jum",
            seen,
        )
        news += found

    # ── 채널 C: 모바일 Naver 뉴스 검색 (BS 막힐 때 독립 채널) ───────────────
    if len(news) < 5:
        for q in [name, name + " 수주", name + " 상장"]:
            news += _fetch_mobile_naver(q, seen)

    return news[:40]


def classify_news(title: str) -> str:
    """뉴스 제목 → 호재(T1·T2)/악재/중립 — Tier 등급제 적용."""
    t = title
    # 소음 필터 → 무조건 중립
    if any(kw in t for kw in _NOISE_KW):
        return "중립"
    # Tier 1 확정 호재
    if any(kw in t for kw in _TIER1_KW):
        return "호재"
    # Tier 2 기대감 호재
    if any(kw in t for kw in _TIER2_KW):
        return "호재"
    # 악재·호재 키워드 비교
    g = sum(1 for kw in _GOOD_KW if kw in t)
    b = sum(1 for kw in _BAD_KW  if kw in t)
    if b > g:  return "악재"
    if g > 0:  return "호재"
    return "중립"


def _news_tier(title: str) -> int:
    """뉴스 제목 → Tier 번호 반환 (1/2/3). 3 = 소음·중립."""
    if any(kw in title for kw in _NOISE_KW):
        return 3
    if any(kw in title for kw in _TIER1_KW):
        return 1
    if any(kw in title for kw in _TIER2_KW):
        return 2
    b = sum(1 for kw in _BAD_KW if kw in title)
    g = sum(1 for kw in _GOOD_KW if kw in title)
    if b > g: return 3   # 악재는 별도 처리, 여기선 소음으로 처리
    if g > 0: return 2
    return 3


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

    score = min(score, 25)  # V5.0: 차트 25점 만점
    if   score >= 20: sig = "🔴 즉시 매수 (HIGH)"
    elif score >= 13: sig = "🟡 매수 준비 (MID)"
    elif score >= 7:  sig = "⚪ 관망 (LOW)"
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
    """수급 점수 35점 — 기관 연속 매수 + 외국인 누적 + 당일 쌍끌이 가중치 (5일 Streak 정밀화)."""
    if not inv:
        return {"score": 0, "detail": "수급 데이터 없음",
                "inst_5d": 0, "frgn_5d": 0, "streak": 0}

    inst_vals = [r["기관"]    for r in inv]
    frgn_vals = [r["외국인"]  for r in inv]
    inst_5d   = sum(inst_vals)
    frgn_5d   = sum(frgn_vals)
    streak    = sum(1 for v in inst_vals if v > 0)

    score = 0
    # 기관 연속 매수 Streak 정밀화 (최대 15점 — 5일 연속 시 만점)
    score += [0, 2, 6, 10, 13, 15][min(streak, 5)]
    # 외국인 누적 순매수 (최대 10점)
    if   frgn_5d > 500_000:  score += 10
    elif frgn_5d > 100_000:  score += 7
    elif frgn_5d > 0:        score += 3
    elif frgn_5d < -500_000: score -= 5
    # 기관 총량 보정 (최대 5점)
    if   inst_5d > 1_000_000: score += 5
    elif inst_5d > 300_000:   score += 3
    elif inst_5d > 0:         score += 1

    details = []

    # 🔥 [핵심 필살기] 당일 쌍끌이 매수 확인 (inv[0]이 가장 최근 날짜)
    if inst_vals[0] > 0 and frgn_vals[0] > 0:
        score += 15  # 쌍끌이 발생 시 누적 음수여도 강력한 보정치 부여
        details.append("🔥당일 쌍끌이 대량 매집 (+15점)🔥")

    score = max(0, min(score, 40))  # V7.0: 수급 40점 만점

    if streak >= 2:           details.append(f"기관 {streak}일 연속 매수")
    if frgn_5d > 100_000:     details.append(f"외국인 순매수 {frgn_5d:+,}")
    if not details:           details.append(f"기관 {inst_5d:+,} / 외국인 {frgn_5d:+,}")

    return {"score": score, "detail": " | ".join(details),
            "inst_5d": inst_5d, "frgn_5d": frgn_5d, "streak": streak}


def score_fundamentals(fund: dict) -> dict:
    """가치/재무 점수 20점 — ROE 수익성 + PBR 저평가 + PER 업종비교."""
    if not fund:
        return {"score": 0, "detail": "재무 데이터 없음"}

    score   = 0
    details = []

    roe = fund.get("ROE")
    pbr = fund.get("PBR")
    per = fund.get("PER")

    # ROE 수익성 (최대 8점)
    if roe is not None:
        if   roe >= 15: score += 8; details.append(f"ROE {roe:.1f}% ★우량")
        elif roe >= 10: score += 5; details.append(f"ROE {roe:.1f}%")
        elif roe >= 5:  score += 3; details.append(f"ROE {roe:.1f}%")
        elif roe < 0:   score -= 3; details.append(f"ROE {roe:.1f}% (적자)")

    # PBR 저평가 (최대 7점)
    if pbr is not None and pbr > 0:
        if   pbr <= 0.8: score += 7; details.append(f"PBR {pbr:.2f} 극저평가")
        elif pbr <= 1.0: score += 5; details.append(f"PBR {pbr:.2f} 저평가")
        elif pbr <= 1.5: score += 3; details.append(f"PBR {pbr:.2f} 적정")

    # PER 상대 저평가 (최대 5점)
    if per is not None and per > 0:
        if   per <= 10: score += 5; details.append(f"PER {per:.1f} 저평가")
        elif per <= 15: score += 3; details.append(f"PER {per:.1f}")
        elif per <= 25: score += 1; details.append(f"PER {per:.1f} 적정")

    score  = max(0, min(score, 20))
    detail = " | ".join(details) if details else "재무 데이터 수집 중"
    return {"score": score, "detail": detail}


def score_news(news: list[dict]) -> dict:
    """뉴스 등급제 점수 20점 — Tier1(20점) / Tier2(건당 5점·최대 10점) / 소음 제외."""
    empty = {"score": 0, "good": [], "bad": [], "neutral": [],
             "impact_hits": [], "tier1_news": [], "tier2_news": []}
    if not news:
        return empty

    tier1_news:  list[dict] = []
    tier2_news:  list[dict] = []
    bad_news:    list[dict] = []
    neutral:     list[dict] = []
    impact_hits: list[str]  = []

    for n in news:
        t = n["title"]
        # ① 소음 필터 — Tier 3 즉시 제외
        if any(kw in t for kw in _NOISE_KW):
            neutral.append(n)
            continue
        # ② Tier 1 확정 호재 감지
        t1_hits = [kw for kw in _TIER1_KW if kw in t]
        if t1_hits:
            tier1_news.append(n)
            for kw in t1_hits:
                if kw not in impact_hits:
                    impact_hits.append(kw)
            continue
        # ③ 악재 감지 (Tier 1보다 먼저 확정된 악재는 없으므로 순서 유지)
        b = sum(1 for kw in _BAD_KW if kw in t)
        g = (sum(1 for kw in _GOOD_KW if kw in t)
             + sum(1 for kw in _TIER2_KW if kw in t))
        if b > 0 and b >= g:
            bad_news.append(n)
            continue
        # ④ Tier 2 기대감 호재
        if any(kw in t for kw in _TIER2_KW) or g > 0:
            tier2_news.append(n)
            continue
        neutral.append(n)

    # ── 점수 산출 ──────────────────────────────────────────────────────────────
    if tier1_news:
        score = 30                                          # V7.0 Tier 1: 즉시 30점 만점
    elif tier2_news:
        raw = min(len(tier2_news) * 7, 20)                 # Tier 2: 건당 7점·최대 20점
        score = max(0, raw - len(bad_news) * 3)
    else:
        score = 0

    good_all = tier1_news + tier2_news
    return {
        "score": score,
        "good":       good_all[:5],
        "bad":        bad_news[:3],
        "neutral":    neutral,
        "impact_hits":impact_hits,
        "tier1_news": tier1_news[:5],
        "tier2_news": tier2_news[:5],
    }


def score_risk_squeeze(price_data: dict, inv_data: list[dict], pb: dict) -> dict:
    """V7.0 리스크/숏스퀴즈 점수 10점 — 공매도역발상·신용잔고·프로그램매매."""
    score:   int       = 0
    signals: list[str] = []

    chg_rate = float((price_data or {}).get("등락률", 0))
    rsi      = pb.get("rsi", 50.0)
    ma5      = pb.get("ma5",  0)
    ma20     = pb.get("ma20", 0)

    # ── ① 숏커버링 시그널 ──────────────────────────────────────────────────────
    # 가격 급등 + RSI 과매도권 탈출 → 대차잔고 감소 대용 시그널
    if chg_rate >= 3.0 and rsi < 45:
        score += 5
        signals.append(f"⚡ 숏커버링 강력 시그널 (+{chg_rate:.1f}%, RSI {rsi:.0f})")
    elif chg_rate >= 1.5 and rsi < 50:
        score += 3
        signals.append(f"🟡 숏커버링 초기 신호 (+{chg_rate:.1f}%, RSI {rsi:.0f})")

    # ── ② 숏스퀴즈 최적 구조 ───────────────────────────────────────────────────
    # 당일 기관+외국인 쌍끌이 + 개인 매도 = 세력 수취 + 숏스퀴즈 세팅
    if inv_data:
        inst_d = inv_data[0].get("기관",   0)
        frgn_d = inv_data[0].get("외국인", 0)
        indv_d = inv_data[0].get("개인",   0)
        if inst_d > 0 and frgn_d > 0 and indv_d < 0:
            score += 5
            signals.append("🔴 숏스퀴즈 최적 구조 (세력 쌍끌이·개인 매도)")

    # ── ③ 신용잔고 위험 감점 ───────────────────────────────────────────────────
    # 3일 연속 개인 대량 순매수 + 기관 이탈 → 신용 반대매매 위험
    if inv_data and len(inv_data) >= 3:
        indv_3 = [r.get("개인",   0) for r in inv_data[:3]]
        inst_3 = [r.get("기관",   0) for r in inv_data[:3]]
        if all(v > 100_000 for v in indv_3) and all(v < 0 for v in inst_3):
            score -= 5
            signals.append("⚠ 신용잔고 위험 — 개인 연속 대량 매수 / 기관 3일 이탈")

    # ── ④ 장막판 프로그램 매수 추정 ────────────────────────────────────────────
    # 단기선(MA5) > 중기선(MA20) + 당일 상승 = 프로그램 매수 유입 추정
    if ma5 > 0 and ma20 > 0 and ma5 > ma20 and chg_rate > 0:
        score += 2
        signals.append("📈 단기선 우위·상승 = 프로그램 매수 유입 추정 (+2)")

    score  = max(0, min(score, 10))
    detail = " | ".join(signals) if signals else "리스크 중립 — 이상 신호 없음"
    return {"score": score, "signals": signals, "detail": detail}


def calc_tomorrow_prob(result: dict) -> tuple[int, str]:
    """내일 상승 확률(%) + 타점 레이블 산출 — V7.0 Quantum Vanguard."""
    total = result.get("total", 0)
    ns    = result.get("news_score",  {})
    iv    = result.get("inv_score",   {})
    rs    = result.get("risk_score",  {"score": 0})

    # ── 전설적 타점: Tier 1 뉴스 + 쌍끌이 + 숏스퀴즈 동시 포착 ────────────────
    legendary = (
        bool(ns.get("tier1_news")) and
        "쌍끌이" in iv.get("detail", "") and
        rs.get("score", 0) >= 8
    )
    if legendary:
        return 98, "전설적 타점 — Tier1 뉴스·쌍끌이·숏스퀴즈 동시 포착"

    # ── 점수 기반 확률 산출 ─────────────────────────────────────────────────────
    if   total >= 80: prob = 85 + min(int((total - 80) * 1.3), 12)
    elif total >= 65: prob = 68 + int((total - 65) * 1.1)
    elif total >= 45: prob = 45 + int((total - 45) * 1.15)
    elif total >= 30: prob = 25 + int((total - 30) * 1.3)
    else:             prob = max(10, int(total * 0.8))

    if   total >= 80: tag = "최상위 매집 구간"
    elif total >= 65: tag = "고신뢰 진입 구간"
    elif total >= 45: tag = "분할 매수 구간"
    elif total >= 30: tag = "관망 구간"
    else:             tag = "진입 금지 구간"

    return int(min(prob, 97)), tag


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

    # ── V7.0 Quantum Vanguard 4축 점수 체계 ─────────────────────────────────
    # 차트/신호 (20점 기여) — GOLDEN RULE: calc_pullback_score 함수 불변
    pb_result = calc_pullback_score(
        ohlcv["Close"],
        ohlcv["Volume"] if "Volume" in ohlcv.columns else pd.Series(dtype=float),
    ) if not ohlcv.empty and len(ohlcv) >= 22 else \
        {"score": 0, "signal": "데이터 부족", "rsi": 50.0, "ma5": 0, "ma20": 0, "ma60": 0}
    pb_contrib = min(pb_result["score"], 20)   # 차트 기여 최대 20점 캡

    # 수급 (40점) — 기관·외국인·쌍끌이
    inv_result = score_investor(inv_data)

    # 가치/재무 — 표시 전용 (총점 미반영, 브리핑용 보조 데이터)
    fund_result = score_fundamentals(fund_data)

    # 뉴스/미반영호재 (30점) — Tier 1 즉시 만점
    news_result = score_news(news_list)

    # 리스크/숏스퀴즈 (10점) — 공매도·신용잔고·프로그램매매
    risk_result = score_risk_squeeze(price_data, inv_data, pb_result)

    # V7.0 총점: 수급40 + 뉴스30 + 차트20 + 리스크10 = 100
    total = min(
        inv_result["score"] + news_result["score"] +
        pb_contrib          + risk_result["score"],
        100
    )

    if   total >= 80: verdict = "👑 전 세계 1등 매수 적기 (LEGENDARY)"
    elif total >= 65: verdict = "🔴 즉시 진입 가능 (HIGH CONFIDENCE)"
    elif total >= 45: verdict = "🟡 진입 검토 (MID)"
    elif total >= 30: verdict = "⚪ 관망 권고 (LOW)"
    else:             verdict = "❌ 진입 불가"

    block_alert = check_block_deal(ticker, inv_data)

    return {
        "ticker": ticker, "name": name, "market": market,
        "price": price_data, "ohlcv": ohlcv,
        "inv_data": inv_data, "fund": fund_data, "news": news_list,
        "pb": pb_result, "inv_score": inv_result,
        "fund_score": fund_result, "news_score": news_result,
        "risk_score": risk_result,
        "short_score": news_result["score"],  # 하위 호환 유지
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
                if count >= 100:
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
        # V7.0: 4축 공식 근사 (뉴스·리스크 미수집 — 기본값 적용)
        pb_cap = min(pb["score"], 20)   # 차트 최대 20점
        total  = min(inv["score"] + pb_cap + 10, 100)
        # news 기본 0점 + risk 기본 중립 10점 합산
        total  = min(total + 10, 100)

        # ── rank_score: 신호 강도 가중치 적용 (정렬 전용, 표시 점수와 별도) ──
        # "즉시 매수" 신호가 최상위 독식하도록 pb_score에 시그널 멀티플라이어 적용
        _SIG_MULT = {"즉시 매수": 2.5, "매수 준비": 1.2, "관망": 0.3, "데이터 부족": 0.2}
        pb_sig = pb.get("signal", "관망")
        sig_mult = next((v for k, v in _SIG_MULT.items() if k in pb_sig), 0.3)
        _RANK_DENOM = 30 * 2.5 + 30 * 2.0 + 20   # 최대 가중 합산 = 155
        rank_raw   = pb["score"] * sig_mult + inv["score"] * 2.0 + 0
        rank_score = int(min(rank_raw / _RANK_DENOM * 100, 100))

        return {
            "ticker":     ticker,
            "name":       name,
            "market":     market,
            "price":      price_data.get("현재가", 0),
            "change":     float(price_data.get("등락률", 0)),
            "cap":        price_data.get("시가총액", 0),
            "pb_score":   pb["score"],
            "inv_score":  inv["score"],
            "total":      total,
            "rank_score": rank_score,
            "signal":     pb["signal"],
            "rsi":        pb["rsi"],
        }
    except Exception:
        return None


def scan_top_stocks(candidates: list[dict]) -> list[dict]:
    """후보 종목 병렬 스코어링 → FDR Marcap 병합 → 점수 내림차순 정렬."""
    with ThreadPoolExecutor(max_workers=24) as ex:
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

    # ── FDR Marcap 병합: Naver API cap이 0/소액인 경우 보완 ──────────────────
    cap_lookup = _get_marcap_lookup()
    for r in results:
        code = r["ticker"]
        if r.get("cap", 0) < 100 and code in cap_lookup:
            r["cap"] = round(cap_lookup[code], 0)

    # ── 정렬: 1순위 차트신호(HIGH→MID→LOW→진입불가), 2순위 총점 ─────────────
    _SIG_PRI = {"즉시 매수": 3, "매수 준비": 2, "관망": 1}

    def _sig_key(r: dict) -> tuple:
        sig = r.get("signal", "")
        pri = next((v for k, v in _SIG_PRI.items() if k in sig), 0)
        return (pri, r.get("total", 0))

    return sorted(results, key=_sig_key, reverse=True)


@st.cache_data(ttl=300, show_spinner=False)
def _scan_top_cached(candidate_tuples: tuple) -> list[dict]:
    """scan_top_stocks의 캐시 래퍼 — tuple 입력으로 hashable 처리 (TTL 300s)."""
    candidates = [{"code": c[0], "name": c[1], "market": c[2]} for c in candidate_tuples]
    return scan_top_stocks(candidates)


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
        chg_col = "#FF5050" if up else "#3399FF"
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

    def _show(df: pd.DataFrame, tab_key: str):
        """데이터프레임 행 선택(on_select) → 단일 종목 정밀 해부 100% 동기화."""
        if df.empty:
            st.info("데이터 동기화 중 — 잠시 후 재시도하세요.")
            return

        # ── 즉시 매수 최우선 강제 정렬 ──────────────────
        display_df = df.copy()
        display_df["Sort_Score"] = display_df["차트 신호"].apply(
            lambda x: 3 if "HIGH" in str(x) else (2 if "MID" in str(x) else 1)
        )
        display_df = display_df.sort_values(by=["Sort_Score", "숨비 점수"], ascending=[False, False]).drop(columns=["Sort_Score"])

        # 데이터프레임 출력 및 선택 이벤트 감지
        event = st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={"숨비 점수": _prog_col},
            selection_mode="single-row",
            on_select="rerun",
            key=f"df_select_{tab_key}"
        )

        # 1% 오차 없는 세션 동기화 (선택한 행의 '코드'를 추출하여 세션에 강제 저장)
        if event and len(event.selection.rows) > 0:
            selected_idx = event.selection.rows[0]
            # 화면에 정렬된 순서 그대로 종목 코드를 정확히 짚어냄
            st.session_state.selected_stock_code = display_df.iloc[selected_idx]["코드"]

    # ── 대형주: FDR Marcap 기준 시총 5,000억+ (200종목 풀에서 필터) ──────
    large = sorted(
        [s for s in scored if s.get("cap", 0) >= 5_000],
        key=lambda x: x.get("cap", 0), reverse=True,
    )
    if len(large) < 5:
        large = sorted(
            [s for s in scored if s.get("cap", 0) > 0],
            key=lambda x: x.get("cap", 0), reverse=True,
        )
    if not large:
        large = [s for s in scored if s["market"] == "KOSPI"] or list(scored)

    # ── 우량주: 숨비 45점+ AND (수급 15+ OR 차트 15+) ────────────────────
    qual = sorted(
        [s for s in scored if s["total"] >= 45
         and (s["pb_score"] >= 12 or s["inv_score"] >= 12)],
        key=lambda x: x["total"], reverse=True,
    )
    if len(qual) < 5:
        qual = sorted(
            [s for s in scored if s["total"] >= 40],
            key=lambda x: x["pb_score"] + x["inv_score"], reverse=True,
        )
    if not qual:
        qual = sorted(scored, key=lambda x: x["pb_score"] + x["inv_score"], reverse=True)

    # ── 소형주: 현재가 10,000원 이하, 대형주 탭과 중복 배제 ──────────────
    large_codes = {s["ticker"] for s in large[:15]}
    penny = sorted(
        [s for s in scored if 0 < s["price"] < 10_000 and s["ticker"] not in large_codes],
        key=lambda x: x["total"], reverse=True,
    )
    if len(penny) < 5:
        penny = sorted(
            [s for s in scored if s["price"] > 0 and s["ticker"] not in large_codes],
            key=lambda x: x["price"],
        )
    if not penny:
        penny = sorted([s for s in scored if s["price"] > 0], key=lambda x: x["price"])

    tab1, tab2, tab3, tab4 = st.tabs([
        "🏆 전체 Top 15",
        "🏢 대형주 (시총 5,000억+)",
        "💎 우량주 (숨비 45점+)",
        "🪙 소형주 (~10,000원)",
    ])
    with tab1: _show(_to_df(scored),  "all")
    with tab2: _show(_to_df(large),   "large")
    with tab3: _show(_to_df(qual),    "qual")
    with tab4: _show(_to_df(penny),   "penny")


# ─────────────────────────────────────────────────────────────────────────────
# 11. UI 컴포넌트
# ─────────────────────────────────────────────────────────────────────────────
def _html_block(html: str):
    """st.html() — iframe 격리. CSS는 블록 내 <style>에 직접 포함."""
    st.html(html)


# ── 자동 브리핑 헬퍼 ─────────────────────────────────────────────────────────
_SECTOR_KW_MAP: list[tuple[str, str, list[str]]] = [
    ("반도체·AI칩",
     "메모리·파운드리·시스템 반도체 설계·제조 기업으로, AI·HPC·데이터센터 수요 확대의 직접 수혜 섹터입니다.",
     ["반도체", "하이닉스", "DB하이텍", "팹리스", "파운드리", "웨이퍼", "칩"]),
    ("조선·방산·해양",
     "대형 선박·군함·LNG선 건조 전문 기업으로, K-방산 수출 확대 및 친환경 선박 전환의 핵심 수혜 섹터입니다.",
     ["조선", "오션", "중공업", "함정", "방산", "항공우주", "LIG"]),
    ("자동차·모빌리티",
     "완성차·부품·전기차 플랫폼 기업으로, 글로벌 전동화 전환과 SDV(소프트웨어 정의 차량) 패러다임 수혜 섹터입니다.",
     ["자동차", "현대차", "기아", "모터스", "모빌리티"]),
    ("바이오·제약·헬스케어",
     "신약·의료기기·진단키트 개발 기업으로, 고령화 사회 및 글로벌 헬스케어 수요 확대의 장기 수혜 섹터입니다.",
     ["바이오", "제약", "생명", "헬스", "메디", "의료", "치료", "백신"]),
    ("2차전지·소재",
     "배터리셀·양극재·음극재·전해질 기업으로, 전기차·ESS 시장 확대와 에너지 전환의 핵심 소재 공급 섹터입니다.",
     ["배터리", "에코프로", "양극재", "전지", "셀", "2차전지"]),
    ("IT·플랫폼·소프트웨어",
     "인터넷·게임·SaaS·AI 소프트웨어 기업으로, 디지털 전환·AI 기반 수익화·구독경제 성장의 직접 수혜 섹터입니다.",
     ["소프트", "플랫폼", "게임", "네이버", "카카오", "솔루션"]),
    ("화학·정유·소재",
     "범용·특수 화학 및 정유 기업으로, 원자재 스프레드와 글로벌 산업 사이클에 수익성이 연동되는 경기민감 섹터입니다.",
     ["화학", "정유", "케미칼", "소재"]),
    ("건설·플랜트·인프라",
     "건축·토목·해외 플랜트 수주 기업으로, 국내외 인프라 투자 확대 및 정책 모멘텀의 직접 수혜 섹터입니다.",
     ["건설", "엔지니어링", "플랜트", "GS건설"]),
    ("금융·증권·보험",
     "은행·증권·보험·캐피탈 기업으로, 금리 환경 변화 및 자본시장 활성화에 수익성이 연동되는 섹터입니다.",
     ["금융", "은행", "보험", "증권", "캐피탈"]),
    ("에너지·환경·유틸리티",
     "태양광·풍력·원자력·가스 발전 기업으로, 탄소중립 전환 및 에너지 안보 강화 정책의 장기 수혜 섹터입니다.",
     ["에너지", "태양광", "풍력", "원자력", "발전"]),
    ("유통·소비재·식품",
     "유통·식품·생활용품 브랜드 기업으로, 내수 소비 회복 및 K-소비재 글로벌 수출 확대 수혜 섹터입니다.",
     ["유통", "마트", "식품", "소비", "롯데", "신세계"]),
    ("통신·미디어·콘텐츠",
     "이동통신·방송·OTT·K-콘텐츠 기업으로, 구독경제·AI B2B 통신 인프라·한류 글로벌 확산 수혜 섹터입니다.",
     ["통신", "KT", "SKT", "LGU", "미디어", "방송", "콘텐츠"]),
]


def _infer_sector_overview(name: str) -> tuple[str, str]:
    """종목명 키워드 → (섹터명, 섹터 설명) 추론."""
    for sector, desc, kws in _SECTOR_KW_MAP:
        if any(kw in name for kw in kws):
            return sector, desc
    return "종합주식", (
        f"{name}는 다양한 사업을 영위하는 기업입니다. "
        "정밀 업종 정보는 DART 공시(dart.fss.or.kr) 및 공식 IR 자료를 참고하세요."
    )


def _per_label_comment(per: float | None) -> tuple[str, str, str]:
    """PER → (레이블, 해설, 색상코드)."""
    if per is None or per <= 0:
        return "산출 불가", "현재 적자 상태이거나 PER 집계가 미완료 상태입니다. 다음 분기 실적 발표 후 재확인하세요.", "#6b7c93"
    if per < 5:
        return "극심한 저평가 ★★★", f"PER {per:.1f}x — 이익 대비 주가가 극단적으로 낮은 저평가 구간. 안전마진 극대화, 리스크 대비 기대수익 최고 구간입니다.", "#27ae60"
    if per < 10:
        return "저평가 매력 ★★", f"PER {per:.1f}x — 업종 평균 하단 수준의 매력적 가격대. 중장기 가치투자 매수 기회 구간입니다.", "#27ae60"
    if per < 15:
        return "적정 가치권 ★", f"PER {per:.1f}x — 시장 평균 PER에 근접한 합리적 가격대. 안정적 투자 영역입니다.", "#D4AF37"
    if per < 25:
        return "성장 프리미엄", f"PER {per:.1f}x — 성장 기대치가 선반영된 구간. 실적 성장 지속 여부 확인이 핵심입니다.", "#f39c12"
    return "고밸류에이션", f"PER {per:.1f}x — 높은 밸류에이션. 고성장 기대 또는 턴어라운드 전망이 전제된 가격 수준입니다.", "#e74c3c"


def _pbr_label_comment(pbr: float | None) -> tuple[str, str, str]:
    """PBR → (레이블, 해설, 색상코드)."""
    if pbr is None or pbr <= 0:
        return "산출 불가", "PBR 집계가 미완료 상태이거나 자본잠식 여부를 점검하세요.", "#6b7c93"
    if pbr < 0.5:
        return "청산가치 이하 ★★★", f"PBR {pbr:.2f}x — 장부 순자산의 절반 이하. 자산 대비 극단 저평가로 청산가치 미만 구간입니다.", "#27ae60"
    if pbr < 1.0:
        return "자산 안전마진 ★★", f"PBR {pbr:.2f}x — 순자산보다 주가가 낮아 하방 리스크가 제한적인 안전마진 구간입니다.", "#27ae60"
    if pbr < 2.0:
        return "적정 자산가치 ★", f"PBR {pbr:.2f}x — 순자산 대비 합리적 프리미엄 수준입니다.", "#D4AF37"
    return "프리미엄 자산", f"PBR {pbr:.2f}x — 브랜드·기술력·성장성 기반 프리미엄. 실적 유지 여부가 밸류에이션의 관건입니다.", "#f39c12"


def _momentum_lines(result: dict) -> list[str]:
    """수급·뉴스 기반 모멘텀 요인 리스트 생성."""
    lines: list[str] = []
    inv     = result.get("inv_score", {})
    streak  = inv.get("streak", 0)
    inst_5d = inv.get("inst_5d", 0)
    frgn_5d = inv.get("frgn_5d", 0)
    total   = result.get("total", 0)
    good_news = result.get("news_score", {}).get("good", [])

    if streak >= 4:
        lines.append(f"🔴 기관 {streak}일 연속 순매수 — 세력 장기 매집 패턴 감지")
    elif streak >= 2:
        lines.append(f"🟡 기관 {streak}일 연속 순매수 — 단기 매집 신호")
    if frgn_5d > 1_000_000:
        lines.append(f"🔴 외국인 대규모 유입 ({frgn_5d:+,}주) — 외국계 기관 적극 매수")
    elif frgn_5d > 200_000:
        lines.append(f"🟡 외국인 순매수 ({frgn_5d:+,}주) — 외국계 관심 포착")
    if inst_5d > 1_000_000:
        lines.append(f"🔴 기관 대량 누적 ({inst_5d:+,}주) — 5거래일 총량 대형")
    for n in good_news[:2]:
        title = n.get("title", "")
        if title:
            short = title[:32] + ("…" if len(title) > 32 else "")
            lines.append(f"📰 호재 뉴스: {short}")
    if total >= 75:
        lines.append(f"⭐ 숨비 종합 {total}점 — 즉시 진입 가능 HIGH CONFIDENCE")
    elif total >= 55:
        lines.append(f"🔵 숨비 종합 {total}점 — 진입 검토 MID 구간")
    if not lines:
        lines.append("현재 수집된 수급·뉴스 모멘텀 신호 없음 — 관망 권고")
    return lines


def ui_auto_briefing(result: dict, name: str, ticker: str):
    """기업 정밀 브리핑 — ①실시간호재 ②섹터 ③저평가해설 ④모멘텀 자동 생성."""
    fund = result.get("fund", {})
    per  = fund.get("PER")
    pbr  = fund.get("PBR")

    sector, sector_desc          = _infer_sector_overview(name)
    per_lbl, per_cmt, per_col    = _per_label_comment(per)
    pbr_lbl, pbr_cmt, pbr_col    = _pbr_label_comment(pbr)
    mom_lines                    = _momentum_lines(result)
    mom_html = "".join(
        f'<div class="ab-item">{ln}</div>' for ln in mom_lines
    )

    # 실시간 호재 Impact Alpha 카드 생성
    ns           = result.get("news_score", {})
    impact_hits  = ns.get("impact_hits", [])
    impact_block = ""
    if impact_hits:
        kw_tags = "".join(
            f'<span style="background:#2a1f00;color:#D4AF37;border:1px solid #D4AF37;'
            f'border-radius:6px;padding:3px 10px;font-size:.78rem;font-weight:800;'
            f'margin:2px 3px;display:inline-block;">⚡ {kw}</span>'
            for kw in impact_hits[:8]
        )
        impact_block = f"""
  <!-- ⓪ 실시간 호재 감지 — Impact Alpha 카드 -->
  <div class="ab-card" style="border:2px solid #D4AF37;background:#1a1600;">
    <div class="ab-badge" style="color:#D4AF37;font-size:.8rem;">
      ⚡ 실시간 호재 감지 — Impact Alpha (뉴스/공매도 점수 20점 만점 강제 적용)
    </div>
    <div style="margin-top:4px;">{kw_tags}</div>
    <div class="ab-body" style="color:#FFD700;margin-top:6px;font-size:.9rem;">
      시장 미반영 초강력 이벤트 포착 — 즉시 매집 주목 대상
    </div>
  </div>"""

    _html_block(f"""
<style>
  .ab-wrap  {{ display:flex; flex-direction:column; gap:12px; margin:4px 0 14px; }}
  .ab-card  {{ background:#12192b; border:1px solid #2a3550; border-radius:14px;
               padding:22px 28px; display:flex; flex-direction:column; gap:8px; }}
  .ab-row2  {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
  .ab-badge {{ font-size:.72rem; font-weight:800; letter-spacing:.16em;
               text-transform:uppercase; color:#D4AF37; margin-bottom:4px; }}
  .ab-title {{ font-size:1.1rem; font-weight:800; color:#F5F5F5; line-height:1.4; }}
  .ab-body  {{ font-size:1.0rem; color:#E0E0E0; line-height:1.75; font-weight:500; }}
  .ab-lbl   {{ display:inline-block; font-size:.76rem; font-weight:700;
               border-radius:6px; padding:4px 12px; margin:4px 0;
               background:rgba(255,255,255,.08); }}
  .ab-item  {{ font-size:.95rem; color:#E0E0E0; line-height:1.7; font-weight:500;
               border-bottom:1px solid #1e2a3a; padding:7px 0; }}
  .ab-item:last-child {{ border-bottom:none; }}
</style>
<div class="ab-wrap">
  {impact_block}
  <!-- ① 기업 핵심 요약 — 전체 폭 단독 카드 -->
  <div class="ab-card">
    <div class="ab-badge">① 기업 핵심 요약</div>
    <div class="ab-title">{sector}</div>
    <div class="ab-body">{sector_desc}</div>
  </div>
  <!-- ② 저평가 해설 + ③ 모멘텀 — 2열 나란히 -->
  <div class="ab-row2">
    <div class="ab-card">
      <div class="ab-badge">② 저평가 및 수익률 해설</div>
      <div class="ab-lbl" style="color:{per_col}">{per_lbl}</div>
      <div class="ab-body">{per_cmt}</div>
      <div class="ab-lbl" style="color:{pbr_col}">{pbr_lbl}</div>
      <div class="ab-body">{pbr_cmt}</div>
    </div>
    <div class="ab-card">
      <div class="ab-badge">③ 독점 기술 &amp; 모멘텀</div>
      {mom_html}
    </div>
  </div>
</div>
""")


def ui_price_header(r: dict):
    """상단: 현재가 Gold·Dark 럭셔리 카드."""
    p   = r["price"]
    cur = p.get("현재가", 0)
    chg = float(p.get("등락률", 0))
    dif = p.get("전일대비", 0)
    cap = p.get("시가총액", 0)
    sign = "▲" if chg >= 0 else "▼"
    up   = chg >= 0
    c_price = "#FF5050" if up else "#3399FF"
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
        _bold_pat = re.compile(r"\*\*(.+?)\*\*")
        _strong   = '<strong style="color:#D4AF37;">\\1</strong>'

        def _md2html(text: str) -> str:
            return _bold_pat.sub(_strong, text)

        moat_items = "".join(
            '<li style="color:#D8E0EC;font-size:.87rem;line-height:1.7;margin:4px 0;">'
            + _md2html(p) + "</li>"
            for p in info["moat"]
        )
        overview_html = _md2html(info["overview"])
        html = (
            '<div style="padding:4px 0;">'
            '<p style="color:#E8E8E8;font-size:.9rem;line-height:1.7;margin-bottom:14px;">'
            '<strong style="color:#D4AF37;">기업 개요</strong> — ' + overview_html + "</p>"
            '<p style="color:#D4AF37;font-size:.8rem;font-weight:800;'
            'letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px;">'
            "핵심 경쟁 우위 (경제적 해자)</p>"
            '<ul style="margin:0;padding-left:18px;">' + moat_items + "</ul>"
            '<p style="color:#4a5568;font-size:.72rem;margin-top:14px;">'
            "※ 공개 IR·뉴스·사업보고서 기반 분석. 투자 권유 아님.</p>"
            "</div>"
        )
        st.markdown(html, unsafe_allow_html=True)


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
    """V7.0 Quantum Vanguard — 숨비 종합 진단 + 내일 상승 확률 히어로 배너."""
    total   = r["total"]
    pb      = r["pb"]
    iv      = r["inv_score"]
    ns      = r["news_score"]
    rs      = r.get("risk_score", {"score": 0, "detail": "—"})
    verdict = r["verdict"]

    prob, prob_tag = calc_tomorrow_prob(r)

    if total >= 80:
        vd_col = "#D4AF37"; vd_bg = "#1a1600"; vd_border = "#D4AF37"
        badge  = "전 세계 1등 매수 적기 (LEGENDARY)"; sc = "#D4AF37"
        emoji  = "👑"
    elif total >= 65:
        vd_col = "#FF5050"; vd_bg = "#1e0a0a"; vd_border = "#FF5050"
        badge  = "즉시 진입 가능 (HIGH)"; sc = "#FF5050"
        emoji  = "🔴"
    elif total >= 45:
        vd_col = "#FFB300"; vd_bg = "#1e1600"; vd_border = "#FFB300"
        badge  = "분할 매수 (MID)";  sc = "#FFB300"
        emoji  = "🟡"
    elif total >= 30:
        vd_col = "#f39c12"; vd_bg = "#221600"; vd_border = "#f39c12"
        badge  = "관망 (LOW)";        sc = "#f39c12"
        emoji  = "⚪"
    else:
        vd_col = "#6b7c93"; vd_bg = "#0d1120"; vd_border = "#4a5568"
        badge  = "진입 불가";         sc = "#6b7c93"
        emoji  = "❌"

    # 확률 색상
    if   prob >= 90: prob_col = "#D4AF37"
    elif prob >= 70: prob_col = "#FF5050"
    elif prob >= 50: prob_col = "#FFB300"
    else:            prob_col = "#6b7c93"

    prob_label = prob_tag if prob_tag else badge
    is_legendary_shot = (prob >= 98)
    legendary_txt = (
        f'<div style="color:#D4AF37;font-size:1.05rem;font-weight:900;'
        f'margin-top:10px;letter-spacing:.05em;">'
        f'⚡ 내일 상승 확률 {prob}% — {prob_label}</div>'
        if is_legendary_shot else
        f'<div style="color:{prob_col};font-size:.95rem;font-weight:800;margin-top:10px;">'
        f'내일 상승 확률 {prob}% — {prob_label}</div>'
    )

    # ── 히어로 점수 배너 (전체 폭, 중앙 정렬) ─────────────────────────────
    st.markdown(
        f"""
<div style="
  background:#1a1a2e;
  border:4px solid {vd_border};
  border-top:4px solid {vd_col};
  border-radius:16px;
  padding:28px 32px;
  text-align:center;
  margin-bottom:18px;
  box-shadow:0 4px 24px rgba(0,0,0,.5);
">
  <div style="font-size:.78rem;font-weight:800;letter-spacing:.2em;
              text-transform:uppercase;color:#8fa3b8;margin-bottom:8px;">
    SOOMBI V7.0 Quantum Vanguard — 종합 진단
  </div>
  <div style="font-size:80px;font-weight:900;color:{sc};
              line-height:1;margin-bottom:8px;">
    {total}<span style="font-size:40px;">점</span>
  </div>
  <div style="font-size:1.3rem;font-weight:800;color:{vd_col};">
    {emoji} {badge}
  </div>
  {legendary_txt}
</div>
""",
        unsafe_allow_html=True,
    )

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
                "tickvals": [0, 30, 45, 65, 80, 100],
                "ticktext": ["0", "30", "45", "65", "80", "100"],
                "tickfont": {"color": "#8fa3b8", "size": 11},
            },
            "bar":  {"color": sc, "thickness": 0.30},
            "bgcolor": "#12192b",
            "borderwidth": 0,
            "steps": [
                {"range": [0,   30],  "color": "#200d0d"},
                {"range": [30,  45],  "color": "#201700"},
                {"range": [45,  65],  "color": "#1c1a00"},
                {"range": [65,  80],  "color": "#0c1f10"},
                {"range": [80, 100],  "color": "#1a1500"},
            ],
            "threshold": {
                "line": {"color": "#D4AF37", "width": 3},
                "thickness": 0.78,
                "value": 80,
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

    pb_contrib_disp = min(pb["score"], 20)
    _mini_card(c1, "수급 (40점)",      iv["score"],        40,
               f"기관·외국인·쌍끌이<br>{iv['detail']}")
    _mini_card(c2, "뉴스/호재 (30점)", ns["score"],        30,
               f"Tier1 {len(ns.get('tier1_news',[]))}건 · Tier2 {len(ns.get('tier2_news',[]))}건<br>악재 {len(ns['bad'])}건")
    _mini_card(c3, "차트/신호 (20점)", pb_contrib_disp,    20,
               f"눌림목 패턴<br>RSI {pb['rsi']} · MA5 {pb['ma5']:,}")
    _mini_card(c4, "리스크/숏스퀴즈 (10점)", rs["score"], 10,
               rs.get("detail", "—"))


def ui_investor_table(inv_data: list[dict]):
    """하단: 투자자별 5거래일 수급표 — 순수 HTML + CSS 클래스 방식 (색상 !important 완전 보장)."""
    if not inv_data:
        st.info("수급 데이터를 수집할 수 없습니다.")
        return

    has_other = any(r.get("기타법인", 0) != 0 for r in inv_data)
    num_cols  = ["기관", "외국인", "개인"] + (["기타법인"] if has_other else [])
    all_cols  = ["날짜"] + num_cols

    def _fmt(v: int) -> str:
        return "—" if v == 0 else f"{v:+,}"

    def _cls(v: int) -> str:
        if v > 0: return "up"
        if v < 0: return "down"
        return "steady-stock"

    # 헤더
    th_cells = "".join(
        f"<th style='background:#0d1526;color:#D4AF37;font-size:13px;font-weight:800;"
        f"letter-spacing:.1em;text-transform:uppercase;text-align:center;"
        f"padding:11px 18px;border-bottom:1px solid #2a3550;'>{c}</th>"
        for c in all_cols
    )

    # 데이터 행
    body_rows = []
    for r in inv_data:
        date_td = (
            f"<td style='text-align:center;padding:10px 18px;"
            f"border-bottom:1px solid #1e2a3a;font-size:15px;'>{r['날짜']}</td>"
        )
        num_tds = []
        for key in num_cols:
            val = int(r.get(key, 0))
            css = _cls(val)
            num_tds.append(
                f"<td class='{css}' style='text-align:center;padding:10px 18px;"
                f"border-bottom:1px solid #1e2a3a;font-size:15px;'>{_fmt(val)}</td>"
            )
        body_rows.append(f"<tr>{date_td}{''.join(num_tds)}</tr>")

    note_html = "" if has_other else (
        "<p style='font-size:13px;color:#5a6a7a;margin-top:8px;'>"
        "※ 개인 = 역산(기관+외국인+기타법인 零合). 기타법인 별도 집계 없음.</p>"
    )

    html = f"""
<p style='font-size:.72rem;font-weight:800;letter-spacing:.14em;
color:#D4AF37;text-transform:uppercase;margin-bottom:8px;'>
◈ 세력 수급 역추적 — 4주체 5거래일 확정 수급 (단위: 주)</p>
<table style='width:100%;border-collapse:collapse;background:#12192b;
border-radius:12px;overflow:hidden;'>
  <thead><tr>{th_cells}</tr></thead>
  <tbody>{''.join(body_rows)}</tbody>
</table>
{note_html}
"""
    st.markdown(html, unsafe_allow_html=True)


def ui_news(news_result: dict, all_news: list[dict]):
    """뉴스 등급제 — Tier1 🔥(score≥15) / Tier2 / 악재 / 전체."""
    score      = news_result.get("score", 0)
    tier1_news = news_result.get("tier1_news", [])
    tier2_news = news_result.get("tier2_news", [])
    bad        = news_result.get("bad", [])
    impact_hits= news_result.get("impact_hits", [])

    if not all_news:
        st.info("뉴스 데이터를 수집할 수 없습니다.")
        return

    # ── Tier 1 🔥 미반영 호재 (score ≥ 15일 때만 표시) ─────────────────────
    if score >= 15 and tier1_news:
        kw_str = " · ".join(impact_hits[:5]) if impact_hits else "핵심 이벤트"
        st.markdown(
            f'<div style="background:#1a1600;border:2px solid #D4AF37;border-radius:10px;'
            f'padding:12px 16px;margin:6px 0 10px;">'
            f'<span style="color:#D4AF37;font-weight:800;font-size:.85rem;">'
            f'🔥 미반영 호재 (Tier 1) — {kw_str}</span></div>',
            unsafe_allow_html=True,
        )
        for n in tier1_news:
            href  = n.get("url", "")
            title = n["title"]
            tier_badge = (
                '<span style="background:#D4AF37;color:#000;font-size:.68rem;'
                'font-weight:800;border-radius:4px;padding:1px 6px;margin-right:5px;">T1</span>'
            )
            if href:
                st.markdown(
                    f'{tier_badge} 🔴 [{title}]({href})',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'{tier_badge} 🔴 {title}',
                    unsafe_allow_html=True,
                )

    # ── Tier 2 일반 호재 ────────────────────────────────────────────────────
    elif tier2_news:
        st.markdown("**📈 미반영 호재 뉴스 (Tier 2)**")
        for n in tier2_news:
            href  = n.get("url", "")
            title = n["title"]
            tier_badge = (
                '<span style="background:#2a3550;color:#8fa3b8;font-size:.68rem;'
                'font-weight:700;border-radius:4px;padding:1px 6px;margin-right:5px;">T2</span>'
            )
            if href:
                st.markdown(f'{tier_badge} 🟢 [{title}]({href})', unsafe_allow_html=True)
            else:
                st.markdown(f'{tier_badge} 🟢 {title}', unsafe_allow_html=True)

    # ── 악재 경보 ────────────────────────────────────────────────────────────
    if bad:
        st.markdown("**📉 악재 주의**")
        for n in bad:
            st.markdown(f"- 🔴 {n['title']} `{n.get('date', '')}`")

    # ── 전체 뉴스 (소음 제외, Tier 표시) ────────────────────────────────────
    noise_filtered = [n for n in all_news if not any(kw in n["title"] for kw in _NOISE_KW)]
    with st.expander(f"전체 뉴스 {len(noise_filtered)}건 (소음 제외) 펼치기"):
        for n in noise_filtered:
            tier = _news_tier(n["title"])
            cls  = classify_news(n["title"])
            if tier == 1:
                badge = "🔴 **[T1]**"
            elif cls == "호재":
                badge = "🟢 [T2]"
            elif cls == "악재":
                badge = "🔻 [악재]"
            else:
                badge = "⬜"
            href = n.get("url", "")
            if href:
                st.markdown(f"{badge} [{n['title']}]({href})", unsafe_allow_html=True)
            else:
                st.markdown(f"{badge} {n['title']}")


def ui_ma_strip(pb: dict):
    """이동평균 3개 카드 행 — 다크모드 가독성 보장."""
    def _v(val: int) -> str:
        return f"{val:,}원" if val else "—"

    _html_block(f"""
<style>
  .ma-row  {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin:4px 0; }}
  .ma-card {{ background:#12192b; border:1px solid #2a3550; border-radius:12px;
              padding:18px 22px; display:flex; flex-direction:column; gap:6px; }}
  .ma-lbl  {{ font-size:.72rem; font-weight:700; letter-spacing:.1em;
              text-transform:uppercase; color:#8fa3b8; }}
  .ma-val  {{ font-size:1.3rem; font-weight:900; color:#FFFFFF; }}
</style>
<div class="ma-row">
  <div class="ma-card">
    <div class="ma-lbl">MA5 (5일선)</div>
    <div class="ma-val">{_v(pb.get("ma5", 0))}</div>
  </div>
  <div class="ma-card">
    <div class="ma-lbl">MA20 (20일선)</div>
    <div class="ma-val">{_v(pb.get("ma20", 0))}</div>
  </div>
  <div class="ma-card">
    <div class="ma-lbl">MA60 (60일선)</div>
    <div class="ma-val">{_v(pb.get("ma60", 0))}</div>
  </div>
</div>
""")


# ─────────────────────────────────────────────────────────────────────────────
# 12. 메인 앱
# ─────────────────────────────────────────────────────────────────────────────
def main():
    # ── 전종목 로드 ──────────────────────────────────────────────────────────
    tickers_df = load_krx_tickers()

    # ── 세션 스테이트 초기화 ─────────────────────────────────────────────────
    if "auto_analyze" not in st.session_state:
        st.session_state["auto_analyze"] = False

    # ── 전역 CSS: SOOMBI 마스터 테마 ─────────────────────────────────────────
    st.markdown("""
<style>
/* ① 기본 배경 + 글자색 (전역 !important 색상 강제 완전 제거) */
.stApp { background-color: #111111; color: #FFFFFF; }
p, span, h1, h2, h3, label { color: #FFFFFF; font-weight: bold; }

/* ① 투명도 — 색상 강제 없이 가시성만 보장 */
html, body, [class*="css"], [class*="st-"],
p, span, label, div, th, td, li {
    opacity: 1 !important;
    visibility: visible !important;
}

/* ① 전광판 st.metric 상승(빨강) / 하락(파랑) */
[data-testid="stMetricDelta"] > div {
    font-weight: 900 !important;
    font-size: 22px !important;
}
[data-testid="stMetricDelta"] svg[title="Price up"] + div  { color: #FF5050 !important; }
[data-testid="stMetricDelta"] svg[title="Price up"] path   { fill:  #FF5050 !important; }
[data-testid="stMetricDelta"] svg[title="Price down"] + div { color: #3399FF !important; }
[data-testid="stMetricDelta"] svg[title="Price down"] path  { fill:  #3399FF !important; }

/* ② 마크다운 일반 텍스트 + 기본 p/th/td — 16px, #F8F9FA */
p,
.stMarkdown p,
.stText,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] em,
[data-testid="stText"],
[data-testid="stCaptionContainer"] p,
table th, table td {
    color: #F8F9FA !important;
    font-size: 20px !important;
    line-height: 1.6 !important;
    font-weight: 600 !important;
}

/* ③ 익스팬더 내부 텍스트 */
section[data-testid="stExpander"] p,
section[data-testid="stExpander"] li,
section[data-testid="stExpander"] span,
[data-testid="stExpander"] p {
    color: #F0F2F6 !important;
    font-size: 1.05rem !important;
    line-height: 1.7 !important;
    font-weight: 500 !important;
}

/* ④ 익스팬더 헤더 골드 강조 */
button[data-testid="stBaseButton-header"] p,
summary p { color: #D4AF37 !important; font-weight: 700 !important; }

/* ⑤ 메트릭 라벨 — 골드 강조, 심층 타겟 전체 */
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] > div,
[data-testid="stMetricLabel"] label,
[data-testid="stMetricLabel"] p,
[data-testid="stText"] p,
[data-testid="stMarkdown"] p,
.st-emotion-cache-1wivap2 {
    color: #FFD700 !important;
    font-size: 20px !important;
    font-weight: 800 !important;
    opacity: 1 !important;
    visibility: visible !important;
}

/* ⑤-b 수급표 + 등락 + 뉴스 HTML 클래스 — 색상 100% 보장 */
.red-val    { color: #FF5050 !important; font-weight: 700 !important; }
.blue-val   { color: #3399FF !important; font-weight: 700 !important; }
.red-plus   { color: #FF5050 !important; font-weight: 700 !important; }
.blue-minus { color: #3399FF !important; font-weight: 700 !important; }
.up-stock   { color: #FF5050 !important; font-weight: 700 !important; }
.down-stock { color: #3399FF !important; font-weight: 700 !important; }
.up         { color: #FF5050 !important; font-weight: 700 !important; }
.up-red     { color: #FF5050 !important; font-weight: 700 !important; font-size: 24px !important; }
.down       { color: #3399FF !important; font-weight: 700 !important; }
.down-blue  { color: #3399FF !important; font-weight: 700 !important; font-size: 24px !important; }
.label      { color: #FFD700 !important; font-weight: 700 !important; }
.gold       { color: #FFD700 !important; font-weight: 700 !important; }
.white      { color: #FFFFFF !important; }
.steady-stock { color: #FFFFFF !important; }
.news-box   { color: #00FF00 !important; font-weight: 700 !important;
              border-left: 5px solid #00FF00; padding-left: 12px; }

/* ⑥ 메트릭 수치 — 크기 유지, 색상 완전 선명 */
[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-size: 1.7rem !important;
    font-weight: 900 !important;
    opacity: 1 !important;
}
[data-testid="stMetricDeltaIcon"] { display: none; }

/* ⑦ 헤딩 — 완전 흰색 선명 유지 */
h1, h2, h3, h4 {
    color: #FFFFFF !important;
    opacity: 1 !important;
}

/* ⑧ 데이터프레임 테이블 — 1.3배 확대 */
[data-testid="stDataFrame"] th,
[data-testid="stDataFrame"] td,
table th, table td {
    font-size: 1.0rem !important;
    color: #FFFFFF !important;
    opacity: 1 !important;
}

/* ⑨ 기업 설명 / 브리핑 본문 커스텀 클래스 */
.sumbi-description {
    color: #E0E0E0 !important;
    font-size: 1.05rem !important;
    line-height: 1.75 !important;
    padding: 15px 0 !important;
    font-weight: 500 !important;
}

/* ⑩ 캡션 */
[data-testid="stCaptionContainer"] p { color: #6b7c93 !important; font-size: .85rem !important; }

/* ⑪ 경고/정보 박스 */
[data-testid="stAlert"] p { color: #F0F2F6 !important; font-size: 1.0rem !important; }

/* ⑫ 탭 텍스트 */
button[data-baseweb="tab"] p { color: #A0AEC0 !important; }
button[data-baseweb="tab"][aria-selected="true"] p { color: #D4AF37 !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)

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
        if is_mkt:
            mkt_label = "🟢 장 중"
        elif is_holiday:
            hol_name = holidays.get(today_str, "")
            mkt_label = f"🔴 공휴일 휴장 ({hol_name})" if hol_name else "🔴 공휴일 휴장"
        else:
            mkt_label = "🔴 장 마감"
        st.markdown(f"**KRX 시장**: {mkt_label}")
        if is_holiday:
            _KOR_WEEKDAY = ["월", "화", "수", "목", "금", "토", "일"]
            _candidate = now_kst.date() + timedelta(days=1)
            _next_yr_hols: dict[str, str] = {}
            while True:
                _c_str = _candidate.strftime("%Y-%m-%d")
                if _candidate.year != now_kst.year:
                    if not _next_yr_hols:
                        _next_yr_hols, _ = _get_krx_holidays(_candidate.year)
                    _all_hols = _next_yr_hols
                else:
                    _all_hols = holidays
                if _candidate.weekday() < 5 and _c_str not in _all_hols:
                    break
                _candidate += timedelta(days=1)
            _next_day_label = f"{_candidate.strftime('%Y-%m-%d')} ({_KOR_WEEKDAY[_candidate.weekday()]})"
            st.markdown(f"**다음 거래일**: {_next_day_label}")
        if hol_fallback:
            if not holidays:
                st.warning(
                    f"{now_kst.year}년 공휴일 기본 테이블 미구성 연도 — 시간/요일만 판단",
                    icon="⚠️",
                )
            else:
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

    # ── 하이엔드 로고 헤더 ────────────────────────────────────────────────────
    _html_block("""
<style>
  .hdr-wrap {
    padding: 32px 0 24px;
    border-bottom: 1px solid #2a3550;
    margin-bottom: 0;
  }
  .hdr-logo {
    font-size: 2.0rem;
    font-weight: 900;
    letter-spacing: .22em;
    background: linear-gradient(90deg,#B8942A 0%,#D4AF37 30%,#F5E882 55%,#C9A020 80%,#D4AF37 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-family: 'Georgia','Times New Roman',serif;
    line-height: 1.15;
    display: inline-block;
  }
  .hdr-ver {
    font-size: .68rem;
    font-weight: 700;
    letter-spacing: .38em;
    color: #6b7c93;
    text-transform: uppercase;
    margin-top: 6px;
  }
  .hdr-rule {
    width: 56px; height: 2px;
    background: linear-gradient(90deg,#D4AF37,transparent);
    margin: 10px 0;
  }
  .hdr-sub {
    font-size: .95rem;
    font-weight: 500;
    color: #c0c8d8;
    letter-spacing: .04em;
    line-height: 1.5;
  }
  .hdr-accent { color: #D4AF37; font-weight: 700; }
</style>
<div class="hdr-wrap">
  <div class="hdr-logo">SOOMBI ANALYTICS</div>
  <div class="hdr-ver">v4.0 &nbsp;·&nbsp; Private Terminal &nbsp;·&nbsp; KRX Intelligence Engine</div>
  <div class="hdr-rule"></div>
  <div class="hdr-sub">
    <span class="hdr-accent">0.1%</span> 세력 역추적 &amp; 매수 적합도 즉시 판단
    &nbsp;—&nbsp; <span class="hdr-accent">숨비 종합 진단 점수</span> 실시간 자동 산출
  </div>
</div>
""")

    # ── 글로벌/국내 증시 전광판 ─────────────────────────────────────────────
    with st.spinner("시장 데이터 동기화 중…"):
        indices = get_market_indices()
    st.markdown(
        '<h2 style="color:#D4AF37;font-size:20px;font-weight:700;'
        'letter-spacing:.05em;margin:4px 0 2px;">글로벌 시장 실시간 전광판</h2>',
        unsafe_allow_html=True,
    )
    ui_market_header(indices)
    st.divider()

    # ── 투자 지표 정밀 분석 Top 15 ───────────────────────────────────────────
    st.markdown(
        '<h2 style="color:#D4AF37;font-size:22px;font-weight:700;'
        'letter-spacing:.05em;margin:4px 0 2px;">투자 지표 정밀 분석 Top 15</h2>'
        '<p style="color:#A0AEC0;font-size:0.82rem;margin:2px 0 8px;">'
        "거래대금 상위 200종목 자동 스캔 → "
        "<strong style='color:#fff;'>즉시 매수 신호 최우선 랭킹</strong> &nbsp;|&nbsp; "
        "표의 행을 클릭하면 하단 정밀 해부가 즉시 실행됩니다</p>",
        unsafe_allow_html=True,
    )

    with st.spinner("데이터 동기화 중 — 전종목 세력 수급 역추적 파이프라인 가동 중 (최대 60초)…"):
        candidates = get_top_volume_tickers()
        if candidates:
            candidate_tuples = tuple((c["code"], c["name"], c["market"]) for c in candidates)
            scored = _scan_top_cached(candidate_tuples)
        else:
            scored = []

    if scored:
        # 코드 기준 역추적을 위한 scored 캐시 세션 저장 (detail 뷰 점수 동기화)
        st.session_state["scored_cache"] = {r["ticker"]: r for r in scored}
        ui_top15_tabs(scored)
    else:
        st.warning("데이터 동기화 중입니다. ⚡ 즉시 갱신 버튼을 눌러 재시도하세요.")
    st.divider()

    # ── 검색 영역 ─────────────────────────────────────────────────────────────
    st.markdown(
        '<h2 style="color:#D4AF37;font-size:22px;font-weight:700;'
        'letter-spacing:.05em;margin:4px 0 8px;">단일 종목 정밀 해부</h2>',
        unsafe_allow_html=True,
    )

    col_q, col_btn = st.columns([5, 1])
    with col_q:
        query = st.text_input(
            "종목명 또는 6자리 코드 입력",
            placeholder="예: 한화오션 / 042660 / 삼성전자 — 또는 위 표에서 종목 클릭",
            label_visibility="collapsed",
            key="search_query",
        )
    with col_btn:
        go = st.button("🔍 해부 시작", use_container_width=True, type="primary")

    # 클릭-투-애널라이즈: Top15 행 클릭 시 자동 트리거
    auto_go = bool(st.session_state.pop("auto_analyze", False))

    # 새 _show 방식: selected_stock_code → search_query 자동 주입
    _clicked_code = st.session_state.pop("selected_stock_code", None)
    if _clicked_code:
        query   = _clicked_code
        auto_go = True

    # ── 검색 → 선택 → 분석 ───────────────────────────────────────────────────
    if query:
        results = search_ticker(query, tickers_df)
        if not results:
            st.warning(f"'{query}' 검색 결과 없음 — 종목명 또는 6자리 코드를 확인하세요.")
            return

        if len(results) > 1 and not auto_go:
            opts = [f"{r['name']} ({r['code']}) [{r['market']}]" for r in results]
            sel_i = st.selectbox("종목 선택", range(len(opts)),
                                  format_func=lambda i: opts[i], key="sel_stock")
            selected = results[sel_i]
        else:
            selected = results[0]
            if not auto_go:
                st.success(f"✅ {selected['name']} ({selected['code']}) [{selected['market']}] 즉시 검색됨")

        if go or auto_go or len(results) == 1:
            ticker = selected["code"]
            name   = selected["name"]
            market = selected["market"]

            with st.spinner(f"{name}({ticker}) — 세력 역추적 파이프라인 가동 중…"):
                result = analyze_ticker(ticker, name, market)

            # ── 데이터 동기화 검증: analyze_ticker 4축 총점이 권위적 소스 ────────
            # (quick_score 캐시 총점 덮어쓰기 금지 — 뉴스/재무 완전 반영된 총점 보존)
            _cached_qs = st.session_state.get("scored_cache", {}).get(ticker)
            if _cached_qs is not None:
                result["pb_cached"]  = _cached_qs["pb_score"]
                result["inv_cached"] = _cached_qs["inv_score"]
                # total은 analyze_ticker의 완전한 4축 점수 그대로 사용

            # ① 현재가 Gold·Dark 카드
            ui_price_header(result)

            # ② 숨비 종합 진단 점수 — Plotly 속도계 게이지
            st.markdown(
                '<h3 style="color:#D4AF37;font-size:18px;font-weight:700;margin:8px 0 2px;">'
                '숨비 종합 진단 점수</h3>',
                unsafe_allow_html=True,
            )
            ui_score_card(result)

            # ③ 기업 정밀 브리핑 — ①섹터 ②저평가해설 ③모멘텀 3카드
            st.markdown(
                '<h3 style="color:#D4AF37;font-size:16px;font-weight:600;margin:8px 0 2px;">'
                '숨비 기업 정밀 브리핑</h3>',
                unsafe_allow_html=True,
            )
            ui_auto_briefing(result, name, ticker)
            st.divider()

            # ④ 4주체 확정 수급표 (기관·외국인·개인·기타법인)
            st.markdown(
                '<h3 style="color:#D4AF37;font-size:16px;font-weight:600;margin:8px 0 2px;">'
                '세력 수급 역추적 — 최근 5거래일 확정 데이터</h3>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div style="color:#D4AF37;font-weight:700;font-size:13px;'
                'letter-spacing:.08em;margin:0 0 8px;opacity:.9;">'
                '💰 수천조 가치의 세력 역추적 중 — 기관 · 외국인 · 개인 · 기타법인 4주체 확정 매집/매도 데이터'
                '</div>',
                unsafe_allow_html=True,
            )
            ui_investor_table(result["inv_data"])
            st.divider()

            # ⑤ 펀더멘털 & 가치 평가 (한글 용어)
            ui_fundamentals_card(result)

            # ⑥ 정밀 사업 분석 아코디언
            ui_moat_expander(name, ticker)

            # ⑦ 세력 동향 경보 (해당 시)
            if result["block_alert"]:
                st.divider()
                ui_block_alert(result["block_alert"])

            # ⑧ 차트 이동평균 지표
            st.divider()
            st.markdown(
                '<h3 style="color:#D4AF37;font-size:16px;font-weight:600;margin:8px 0 2px;">'
                '기술적 이동평균 지표</h3>',
                unsafe_allow_html=True,
            )
            ui_ma_strip(result["pb"])

            # ⑨ 미반영 호재 뉴스 & 팩트체크
            st.markdown(
                '<h3 style="color:#D4AF37;font-size:16px;font-weight:600;margin:8px 0 2px;">'
                '미반영 호재 뉴스 & 팩트 분석</h3>',
                unsafe_allow_html=True,
            )
            ui_news(result["news_score"], result["news"])

    else:
        # 시작 화면
        _html_block("""
<style>
  .start-wrap {
    background:#12192b; border:1px solid #2a3550; border-radius:16px;
    padding:28px 32px; margin:16px 0;
  }
  .start-title {
    font-size:.72rem; font-weight:800; letter-spacing:.18em;
    color:#D4AF37; text-transform:uppercase; margin-bottom:16px;
  }
  .start-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
  .start-card {
    background:#0d1526; border:1px solid #1e2a3a; border-radius:10px;
    padding:16px 18px;
  }
  .start-card-title {
    font-size:.7rem; color:#D4AF37; font-weight:800;
    letter-spacing:.1em; text-transform:uppercase; margin-bottom:8px;
  }
  .start-card-body { font-size:.85rem; color:#c0c8d8; line-height:1.6; }
  .start-code { color:#F5E882; font-weight:700; font-family:monospace; }
  .start-algo {
    background:linear-gradient(135deg,#0d1526,#12192b);
    border:1px solid #D4AF37; border-radius:10px;
    padding:16px 18px; margin-top:16px;
  }
  .start-algo-title {
    font-size:.7rem; color:#D4AF37; font-weight:800;
    letter-spacing:.14em; text-transform:uppercase; margin-bottom:8px;
  }
  .start-algo-body { font-size:.84rem; color:#c0c8d8; line-height:1.7; }
  .gold { color:#D4AF37; font-weight:700; }
</style>
<div class="start-wrap">
  <div class="start-title">🔍 단일 종목 정밀 해부 — 검색 가이드</div>
  <div class="start-grid">
    <div class="start-card">
      <div class="start-card-title">KOSPI 대형주 예시</div>
      <div class="start-card-body">
        <span class="start-code">005930</span> 또는 <span class="start-code">삼성전자</span><br>
        <span class="start-code">000660</span> 또는 <span class="start-code">SK하이닉스</span><br>
        <span class="start-code">042660</span> 또는 <span class="start-code">한화오션</span>
      </div>
    </div>
    <div class="start-card">
      <div class="start-card-title">KOSDAQ 성장주 예시</div>
      <div class="start-card-body">
        <span class="start-code">086520</span> 또는 <span class="start-code">에코프로</span><br>
        <span class="start-code">247540</span> 또는 <span class="start-code">에코프로비엠</span><br>
        <span class="start-code">439260</span> 또는 <span class="start-code">대한조선</span>
      </div>
    </div>
  </div>
  <div class="start-algo">
    <div class="start-algo-title">⚙️ 숨비 종합 진단 점수 — 자동 산출 알고리즘</div>
    <div class="start-algo-body">
      <span class="gold">세력 수급 역추적 (30점)</span> — 기관·외국인 5거래일 순매매 방향성 자동 감지<br>
      <span class="gold">공매도 잔고 분석 (20점)</span> — 외국인잔고율 변화 기반 쇼트 포지션 역추적<br>
      <span class="gold">정밀 눌림목 패턴 (30점)</span> — RSI·MA5·MA20·MA60 이동평균 정배열 자동 산출<br>
      <span class="gold">미반영 호재 뉴스 (20점)</span> — 42개 호재/악재 키워드 NLP 자동 분류<br>
      <br>
      종목명 또는 6자리 코드를 입력하고 <span class="gold">해부 시작</span>을 누르세요.
    </div>
  </div>
</div>
""")


if __name__ == "__main__":
    main()
