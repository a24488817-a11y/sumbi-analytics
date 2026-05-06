"""
숨비 애널리틱스 v3.0 (SOOMBI Analytics)
- 시장 분리 랭킹: KOSPI TOP 15 / KOSDAQ TOP 15
- 종목 체급 자동 분류: 👑대장주(시총1조+) / ⚖️중형주(2천억~1조) / 🪙소형/동전주(2천억미만·주가2천원미만)
- 내일 급등 확률: 기대수익률 + 승률 계산
- 4대 필살기: 기관/연기금 × 공매도상환 × 눌림목 × 미반영호재
"""

import re
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from streamlit_autorefresh import st_autorefresh
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="숨비 애널리틱스 · SOOMBI Analytics",
    page_icon="🐳",
    layout="wide",
)

# ───────────────────────────────────────────────────────────────────────────────
# CSS — 토스증권 스타일 + 체급 뱃지
# ───────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Pretendard','Noto Sans KR',sans-serif; }
.main { background: #f8f9fc; }

/* 지수 카드 — 컴팩트 */
.index-card { background:#fff; border-radius:12px; padding:10px 14px;
    box-shadow:0 1px 6px rgba(0,0,0,0.06); margin-bottom:0; border:1px solid #f0f0f5; }
.index-name  { font-size:10px; font-weight:700; color:#8c8c9e; letter-spacing:.4px; margin-bottom:1px; }
.index-value { font-size:18px; font-weight:900; color:#13131a; line-height:1.2; }
.index-delta { font-size:11px; font-weight:700; margin-top:2px; }
.up   { color:#ef4444; }
.down { color:#1d6ce8; }
.flat { color:#9ca3af; }

/* 섹션 */
.section-header { font-size:20px; font-weight:800; color:#13131a; margin:28px 0 6px; letter-spacing:-.3px; }
.section-sub    { font-size:13px; color:#8c8c9e; margin-bottom:16px; }

/* ── 종목 카드 ── */
.stock-card { background:#fff; border-radius:16px; padding:20px 22px;
    margin-bottom:10px; box-shadow:0 2px 10px rgba(0,0,0,0.06); border-left:5px solid #e2e8f0; }
.stock-card.tier1 { border-left-color:#ef4444; }
.stock-card.tier2 { border-left-color:#f97316; }
.stock-card.tier3 { border-left-color:#eab308; }
.stock-card.tier4 { border-left-color:#94a3b8; }
.stock-rank  { font-size:13px; font-weight:700; color:#8c8c9e; }
.stock-name  { font-size:19px; font-weight:800; color:#13131a; margin:2px 0 4px; }
.stock-sector { font-size:12px; color:#9ca3af; background:#f1f5f9; border-radius:6px;
    padding:2px 8px; display:inline-block; }

/* ── 체급 뱃지 (크게!) ── */
.grade-badge { font-size:15px; font-weight:800; border-radius:12px;
    padding:6px 14px; display:inline-flex; align-items:center; gap:5px; }
.grade-bluechip { background:#7c3aed; color:#fff; }
.grade-midcap   { background:#059669; color:#fff; }
.grade-small    { background:#d97706; color:#fff; }

/* ── 내일 예측 박스 ── */
.forecast-box { background:#f8fafc; border-radius:12px; padding:12px 16px;
    border:1px solid #e2e8f0; text-align:center; }
.forecast-rate { font-size:22px; font-weight:900; }
.forecast-label { font-size:11px; color:#9ca3af; margin-top:2px; }
.win-rate-pill  { display:inline-block; background:#f0fdf4; color:#16a34a;
    border-radius:8px; padding:3px 10px; font-size:13px; font-weight:800; }

/* 신호등 */
.signal-buy  { background:#ef4444; color:#fff; border-radius:10px;
    padding:4px 14px; font-size:13px; font-weight:800; }
.signal-ready{ background:#f59e0b; color:#fff; border-radius:10px;
    padding:4px 14px; font-size:13px; font-weight:800; }
.signal-wait { background:#94a3b8; color:#fff; border-radius:10px; padding:4px 14px; font-size:13px; }
.signal-stop { background:#e2e8f0; color:#64748b; border-radius:10px; padding:4px 14px; font-size:13px; }

/* 배지 */
.badge { display:inline-block; border-radius:8px; padding:3px 10px;
    font-size:12px; font-weight:700; margin:2px 3px 2px 0; }
.badge-inst    { background:#fef2f2; color:#dc2626; }
.badge-short   { background:#fff7ed; color:#ea580c; }
.badge-pb      { background:#f0fdf4; color:#16a34a; }
.badge-news    { background:#eff6ff; color:#2563eb; }
.badge-safe    { background:#dbeafe; color:#1d4ed8; }
.badge-explode { background:#7c3aed; color:#fff; }

/* 적합도 바 */
.fit-bar-wrap { background:#f1f5f9; border-radius:99px; height:7px; margin:7px 0 3px; }
.fit-bar      { border-radius:99px; height:7px; }

/* 매크로 카드 */
.macro-card { background:#fff; border-radius:16px; padding:20px 24px;
    box-shadow:0 2px 10px rgba(0,0,0,0.06); margin-bottom:12px; }

/* 타이틀 */
.soombi-title { font-size:32px; font-weight:900; color:#13131a; letter-spacing:-1px; }
.soombi-sub   { font-size:14px; color:#8c8c9e; margin-top:2px; }

/* 사이드바 */
section[data-testid="stSidebar"] { background:#fff; border-right:1px solid #f0f0f5; }

/* 시장 상태 뱃지 */
.market-status-badge {
    display:flex; align-items:center; gap:8px;
    border-radius:12px; padding:10px 14px;
    border:1px solid; margin:4px 0 8px;
    font-family:'Pretendard','Noto Sans KR',sans-serif;
}
.market-status-dot { font-size:16px; line-height:1; }
.market-status-text { flex:1; }
.market-status-label      { font-size:13px; font-weight:800; line-height:1.3; }
.market-status-time       { font-size:11px; color:#9ca3af; margin-top:1px; }
.market-status-countdown  { font-size:12px; font-weight:700; margin-top:4px; }

/* 버튼 */
.stButton > button {
    background:linear-gradient(135deg,#ef4444 0%,#dc2626 100%) !important;
    color:white !important; font-weight:800 !important; border-radius:14px !important;
    border:none !important; padding:14px 28px !important; font-size:16px !important;
    width:100%; box-shadow:0 4px 15px rgba(239,68,68,.4) !important; }

[data-testid="stTabs"] button { font-weight:700; font-size:14px; }
[data-testid="stTabs"] button[aria-selected="true"] {
    color:#ef4444 !important; border-bottom-color:#ef4444 !important; }
thead tr th { background:#f8fafc !important; font-weight:700 !important;
    font-size:13px !important; color:#374151 !important; }

/* 스나이퍼 검색 헤더 */
.sniper-header { background:linear-gradient(135deg,#1e1e2e 0%,#0f172a 100%);
    border-radius:16px; padding:16px 22px 12px; margin:10px 0 6px; }
.sniper-title { font-size:15px; font-weight:900; color:#f8fafc; letter-spacing:-.3px; }
.sniper-sub   { font-size:11px; color:#94a3b8; margin-top:3px; }

/* 스나이퍼 결과 카드 */
.sniper-card { background:#fff; border-radius:20px; padding:22px 26px;
    box-shadow:0 6px 24px rgba(0,0,0,0.10); margin:6px 0 14px; border:1px solid #f0f0f5; }
.sniper-name { font-size:22px; font-weight:900; color:#13131a; }
.sniper-meta { font-size:12px; color:#8c8c9e; margin:2px 0 8px; }

/* 4대 필살기 스코어 박스 */
.filter-box   { background:#f8fafc; border-radius:12px; padding:12px 14px;
    text-align:center; border:1px solid #e2e8f0; }
.filter-name  { font-size:11px; font-weight:700; color:#8c8c9e; margin-bottom:5px; }
.filter-score { font-size:26px; font-weight:900; line-height:1.1; }
.filter-max   { font-size:10px; color:#c4c4cf; margin-top:2px; }

/* MA 분석 */
.ma-row   { display:flex; align-items:center; gap:10px; margin-bottom:5px; font-size:13px; }
.ma-label { font-weight:700; min-width:44px; color:#6b7280; }
.ma-val   { font-weight:800; color:#13131a; }

/* 뉴스 분류 카드 */
.nc-good { background:#f0fdf4; border-radius:10px; padding:9px 14px;
    border-left:3px solid #16a34a; margin-bottom:6px; font-size:13px; color:#14532d; }
.nc-bad  { background:#fef2f2; border-radius:10px; padding:9px 14px;
    border-left:3px solid #dc2626; margin-bottom:6px; font-size:13px; color:#7f1d1d; }
.nc-neut { background:#f8fafc; border-radius:10px; padding:9px 14px;
    border-left:3px solid #94a3b8; margin-bottom:6px; font-size:13px; color:#475569; }
</style>
""", unsafe_allow_html=True)


# ───────────────────────────────────────────────────────────────────────────────
# 종목 DB
# ───────────────────────────────────────────────────────────────────────────────
KOSPI_STOCKS = {
    "005930": ("삼성전자",         "반도체/IT"),
    "000660": ("SK하이닉스",       "반도체/IT"),
    "035420": ("NAVER",            "인터넷/플랫폼"),
    "005380": ("현대차",           "자동차"),
    "051910": ("LG화학",           "화학/배터리"),
    "006400": ("삼성SDI",          "화학/배터리"),
    "068270": ("셀트리온",         "바이오/헬스케어"),
    "105560": ("KB금융",           "금융"),
    "028260": ("삼성물산",         "건설/산업재"),
    "012330": ("현대모비스",       "자동차"),
    "207940": ("삼성바이오로직스", "바이오/헬스케어"),
    "000270": ("기아",             "자동차"),
    "017670": ("SK텔레콤",         "통신"),
    "030200": ("KT",               "통신"),
    "015760": ("한국전력",         "에너지/유틸리티"),
    "034730": ("SK",               "지주/복합"),
    "032830": ("삼성생명",         "금융"),
    "086790": ("하나금융지주",     "금융"),
    "009540": ("HD현대중공업",     "조선/기계"),
    "010950": ("S-Oil",            "에너지/유틸리티"),
    "055550": ("신한지주",         "금융"),
    "024110": ("기업은행",         "금융"),
    "066570": ("LG전자",           "가전/전자"),
    "003550": ("LG",               "지주/복합"),
    "011200": ("HMM",              "운송/물류"),
    "034220": ("LG디스플레이",     "반도체/IT"),
    "009830": ("한화솔루션",       "화학/배터리"),
    "000100": ("유한양행",         "바이오/헬스케어"),
    "035720": ("카카오",           "인터넷/플랫폼"),
    "003490": ("대한항공",         "운송/물류"),
    "097950": ("CJ제일제당",       "소비재/음식"),
    "004020": ("현대제철",         "철강/소재"),
    "010130": ("고려아연",         "철강/소재"),
    "028050": ("삼성엔지니어링",   "건설/산업재"),
    "267250": ("HD현대",           "지주/복합"),
    "009150": ("삼성전기",         "반도체/IT"),
    "090430": ("아모레퍼시픽",     "소비재/음식"),
    "004170": ("신세계",           "유통/소비"),
    "004000": ("롯데케미칼",       "화학/배터리"),
    "005490": ("POSCO홀딩스",      "철강/소재"),
    "000810": ("삼성화재",         "금융"),
    "078930": ("GS",               "지주/복합"),
    "036460": ("한국가스공사",     "에너지/유틸리티"),
    "000720": ("현대건설",         "건설/산업재"),
    "016360": ("삼성증권",         "금융"),
    "139480": ("이마트",           "유통/소비"),
    "006800": ("미래에셋증권",     "금융"),
    "042660": ("한화오션",         "조선/기계"),
    "352820": ("하이브",           "엔터/미디어"),
    "035900": ("JYP엔터테인먼트",  "엔터/미디어"),
    "041510": ("SM엔터테인먼트",   "엔터/미디어"),
    "326030": ("SK바이오팜",       "바이오/헬스케어"),
    "033780": ("KT&G",             "소비재/음식"),
    "003670": ("포스코퓨처엠",     "화학/배터리"),
    "064350": ("현대로템",         "조선/기계"),
    "229640": ("LS ELECTRIC",      "전력/전기"),
    "069960": ("현대백화점",       "유통/소비"),
    "011780": ("금호석유",         "화학/배터리"),
    "011070": ("LG이노텍",         "반도체/IT"),
    "010140": ("삼성중공업",       "조선/기계"),
    "071050": ("한국금융지주",     "금융"),
    "377300": ("카카오페이",       "인터넷/플랫폼"),
    "112610": ("씨에스윈드",       "신재생에너지"),
    "008770": ("호텔신라",         "유통/소비"),
}

KOSDAQ_STOCKS = {
    "247540": ("에코프로비엠",       "화학/배터리"),
    "086520": ("에코프로",           "화학/배터리"),
    "196170": ("알테오젠",           "바이오/헬스케어"),
    "263750": ("펄어비스",           "게임"),
    "293490": ("카카오게임즈",       "게임"),
    "068760": ("셀트리온제약",       "바이오/헬스케어"),
    "028300": ("HLB",                "바이오/헬스케어"),
    "045020": ("코스맥스",           "소비재/음식"),
    "214150": ("클래시스",           "의료기기"),
    "064760": ("티씨케이",           "반도체/IT"),
    "357780": ("솔브레인",           "반도체/IT"),
    "030520": ("한글과컴퓨터",       "반도체/IT"),
    "053800": ("안랩",               "반도체/IT"),
    "145720": ("덴티움",             "의료기기"),
    "068600": ("대원제약",           "바이오/헬스케어"),
    "323410": ("카카오뱅크",         "금융"),
    "039030": ("이오테크닉스",       "반도체/IT"),
    "131970": ("테크윙",             "반도체/IT"),
    "240810": ("원익IPS",            "반도체/IT"),
    "058470": ("리노공업",           "반도체/IT"),
    "009420": ("한올바이오파마",     "바이오/헬스케어"),
    "078340": ("컴투스",             "게임"),
    "036830": ("솔브레인홀딩스",     "화학/배터리"),
    "048260": ("오스템임플란트",     "의료기기"),
    "122870": ("와이지엔터테인먼트", "엔터/미디어"),
    "067160": ("아프리카TV",         "인터넷/플랫폼"),
    "108490": ("로보티즈",           "로봇/AI"),
}

# ───────────────────────────────────────────────────────────────────────────────
# KRX 시장 상태 — 한국 표준시(KST = UTC+9) 기반
# ───────────────────────────────────────────────────────────────────────────────
KST = timezone(timedelta(hours=9))

from datetime import date as _date

# KRX-observed public holidays by year (update annually).
# Includes substitute holidays (대체공휴일) when the original falls on a weekend.
_KRX_HOLIDAYS: dict[int, frozenset[_date]] = {
    2025: frozenset({
        _date(2025,  1,  1),   # 신정
        _date(2025,  1, 28),   # 설날 연휴 (전날)
        _date(2025,  1, 29),   # 설날
        _date(2025,  1, 30),   # 설날 연휴 (다음날)
        _date(2025,  3,  3),   # 삼일절 대체공휴일 (3/1 토요일)
        _date(2025,  5,  5),   # 어린이날
        _date(2025,  5,  6),   # 석가탄신일 대체공휴일 (5/5 중복)
        _date(2025,  6,  6),   # 현충일
        _date(2025,  8, 15),   # 광복절
        _date(2025, 10,  3),   # 개천절
        _date(2025, 10,  6),   # 추석
        _date(2025, 10,  7),   # 추석 연휴 (다음날)
        _date(2025, 10,  8),   # 추석 대체공휴일 (10/5 전날 일요일)
        _date(2025, 10,  9),   # 한글날
        _date(2025, 12, 25),   # 성탄절
    }),
    2026: frozenset({
        _date(2026,  1,  1),   # 신정
        _date(2026,  2, 16),   # 설날 연휴 (전날)
        _date(2026,  2, 17),   # 설날
        _date(2026,  2, 18),   # 설날 연휴 (다음날)
        _date(2026,  3,  2),   # 삼일절 대체공휴일 (3/1 일요일)
        _date(2026,  5,  1),   # 근로자의 날 (KRX 휴장)
        _date(2026,  5,  5),   # 어린이날
        _date(2026,  5, 25),   # 석가탄신일 (음력 4월 8일)
        _date(2026,  6,  6),   # 현충일 (토요일)
        _date(2026,  6,  8),   # 현충일 대체공휴일
        _date(2026,  8, 15),   # 광복절 (토요일)
        _date(2026,  8, 17),   # 광복절 대체공휴일
        _date(2026,  9, 23),   # 추석 연휴 (전날)
        _date(2026,  9, 24),   # 추석
        _date(2026,  9, 25),   # 추석 연휴 (다음날)
        _date(2026, 10,  3),   # 개천절 (토요일)
        _date(2026, 10,  5),   # 개천절 대체공휴일
        _date(2026, 10,  9),   # 한글날
        _date(2026, 12, 25),   # 성탄절
    }),
}

_warned_missing_years: set[int] = set()


@st.cache_data(ttl=86_400, show_spinner=False)
def _fetch_krx_holidays_api(year: int) -> frozenset | None:
    """Fetch KRX non-trading days for *year* from the KRX open-data portal.

    Uses the two-step OTP flow:
      1. GET  GenerateOTP.jspx  → one-time code
      2. POST OPN99000001.jspx  → JSON with block1[] rows, each having a calnd_dd field (YYYYMMDD)

    Retries up to 3 times (with exponential back-off: 1 s, 2 s) on transient
    network / 5xx errors.  Permanent 4xx responses are not retried.

    Returns a frozenset of date objects on success, or None on any
    network/parse error so callers can fall back to the hardcoded table.
    """
    import time as _time

    _TRANSIENT_EXC = (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.ChunkedEncodingError,
    )
    # Timing budget: 3 attempts × (2 s OTP + 2 s POST) + back-off (1 s + 2 s) = 15 s worst case
    _MAX_ATTEMPTS = 3
    _BACKOFF_BASE = 1.0
    _PER_REQUEST_TIMEOUT = 2

    last_exc: Exception | None = None

    for attempt in range(_MAX_ATTEMPTS):
        if attempt > 0:
            _time.sleep(_BACKOFF_BASE * (2 ** (attempt - 1)))

        try:
            sess = requests.Session()
            sess.headers.update({
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                "Referer": "http://open.krx.co.kr/",
            })

            otp_resp = sess.get(
                "https://open.krx.co.kr/contents/COM/GenerateOTP.jspx",
                params={"bld": "MKD/01/0110/01100305/mkd01100305", "name": "form"},
                timeout=_PER_REQUEST_TIMEOUT,
            )
            otp_resp.raise_for_status()
            otp = otp_resp.text.strip()
            if not otp:
                return None

            data_resp = sess.post(
                "https://open.krx.co.kr/contents/OPN/99/OPN99000001.jspx",
                data={"search_bas_yy": str(year), "code": otp},
                timeout=_PER_REQUEST_TIMEOUT,
            )
            data_resp.raise_for_status()
            payload = data_resp.json()

            holidays: set[_date] = set()
            for row in payload.get("block1", []):
                raw = row.get("calnd_dd", "")
                if len(raw) == 8:
                    try:
                        holidays.add(_date(int(raw[:4]), int(raw[4:6]), int(raw[6:])))
                    except ValueError:
                        pass

            return frozenset(holidays) if holidays else None

        except requests.exceptions.HTTPError as _exc:
            resp = _exc.response
            if resp is not None and 400 <= resp.status_code < 500:
                import warnings as _w
                _w.warn(
                    f"KRX holiday API returned {resp.status_code} for {year} — "
                    "permanent error, not retrying. Falling back to hardcoded table.",
                    stacklevel=2,
                )
                return None
            last_exc = _exc

        except _TRANSIENT_EXC as _exc:
            last_exc = _exc

        except Exception as _exc:
            import warnings as _w
            _w.warn(
                f"KRX holiday API fetch failed for {year}: {type(_exc).__name__}: {_exc}. "
                "Falling back to hardcoded holiday table.",
                stacklevel=2,
            )
            return None

    import warnings as _w
    _w.warn(
        f"KRX holiday API fetch failed for {year} after {_MAX_ATTEMPTS} attempts: "
        f"{type(last_exc).__name__}: {last_exc}. Falling back to hardcoded holiday table.",
        stacklevel=2,
    )
    return None


def _get_krx_holidays(year: int) -> frozenset[_date]:
    """Return the holiday set for *year*, preferring the live KRX API.

    Fall-back chain:
      1. Live KRX open-data API (cached 24 h via st.cache_data)
      2. Hardcoded _KRX_HOLIDAYS table
      3. Empty set (with a one-time warning)
    """
    live = _fetch_krx_holidays_api(year)
    if live is not None:
        return live

    fallback = _KRX_HOLIDAYS.get(year)
    if fallback is not None:
        return fallback

    if year not in _warned_missing_years:
        import warnings as _warnings
        _warnings.warn(
            f"KRX holiday calendar: live API unavailable and no hardcoded fallback for {year}. "
            "Market-status badge may treat public holidays as trading days.",
            stacklevel=2,
        )
        _warned_missing_years.add(year)
    return frozenset()


def _is_krx_holiday(d: _date) -> bool:
    """Return True if *d* is a KRX-observed public holiday."""
    return d in _get_krx_holidays(d.year)


def _next_trading_open_minutes(now_kst: datetime) -> int:
    """Return minutes from now_kst until the next KRX regular session open (09:00 KST).

    Searches up to 14 days ahead, skipping weekends and KRX holidays.
    Uses concrete datetime arithmetic so multi-day gaps (e.g. Friday → Monday,
    or multi-day holiday spans) are handled correctly.
    """
    from datetime import timedelta as _td
    candidate = now_kst.date()
    for _ in range(14):
        if candidate.weekday() < 5 and not _is_krx_holiday(candidate):
            target = datetime(
                candidate.year, candidate.month, candidate.day,
                9, 0, 0, tzinfo=KST
            )
            if target > now_kst:
                return int((target - now_kst).total_seconds() // 60)
        candidate += _td(days=1)
    return 0


def get_krx_market_status() -> dict:
    """
    Returns a dict with:
      status        : "open" | "pre" | "after" | "closed"
      label         : Korean display text
      emoji         : status emoji
      color         : hex color for badge
      time_kst      : current KST time string (HH:MM)
      countdown_text: Korean countdown string, e.g. "30분 후 개장" or "45분 후 마감"
    """
    now_kst = datetime.now(KST)
    weekday = now_kst.weekday()   # 0=Mon … 4=Fri, 5=Sat, 6=Sun
    t = now_kst.hour * 60 + now_kst.minute   # minutes since midnight KST
    today = now_kst.date()

    if weekday >= 5:
        return {"status": "closed", "label": "휴장 (주말)",
                "emoji": "⚫", "color": "#6b7280",
                "time_kst": now_kst.strftime("%H:%M"),
                "countdown_text": ""}

    if _is_krx_holiday(today):
        mins = _next_trading_open_minutes(now_kst)
        countdown = f"{mins}분 후 개장" if mins > 0 else ""
        return {"status": "closed", "label": "휴장 (공휴일)",
                "emoji": "⚫", "color": "#6b7280",
                "time_kst": now_kst.strftime("%H:%M"),
                "countdown_text": countdown}

    # Pre-market:   08:00 – 09:00
    # Regular:      09:00 – 15:30
    # After-hours:  15:30 – 18:00
    # Closed:       otherwise
    if 8 * 60 <= t < 9 * 60:
        mins = 9 * 60 - t
        return {"status": "pre", "label": "장 시작 전 (Pre-market)",
                "emoji": "🟡", "color": "#f59e0b",
                "time_kst": now_kst.strftime("%H:%M"),
                "countdown_text": f"{mins}분 후 개장"}
    elif 9 * 60 <= t < 15 * 60 + 30:
        mins = (15 * 60 + 30) - t
        return {"status": "open", "label": "정규장 운영 중 (Open)",
                "emoji": "🟢", "color": "#16a34a",
                "time_kst": now_kst.strftime("%H:%M"),
                "countdown_text": f"{mins}분 후 마감"}
    elif 15 * 60 + 30 <= t < 18 * 60:
        mins = _next_trading_open_minutes(now_kst)
        countdown = f"{mins}분 후 개장" if mins > 0 else ""
        return {"status": "after", "label": "장 마감 후 (After-hours)",
                "emoji": "🟠", "color": "#ea580c",
                "time_kst": now_kst.strftime("%H:%M"),
                "countdown_text": countdown}
    else:
        mins = _next_trading_open_minutes(now_kst)
        countdown = f"{mins}분 후 개장" if mins > 0 else ""
        return {"status": "closed", "label": "장 마감 (Closed)",
                "emoji": "⚫", "color": "#6b7280",
                "time_kst": now_kst.strftime("%H:%M"),
                "countdown_text": countdown}


OVERHANG_DB = {
    "042660": {"type": "블록딜(PRS)", "safe": True,
               "comment": "대형 블록딜이지만 전략적 투자자 유치 목적. 하방 경직성 확보 '안전핀' 패턴."},
    "003670": {"type": "CB 전환",    "safe": True,
               "comment": "전환사채 물량 상존. 포스코그룹 지원 시 하방 지지선 역할."},
    "086520": {"type": "CB/블록딜",  "safe": False,
               "comment": "에코프로그룹 CB 물량 상존. 급등 시 차익실현 출회 주의."},
    "247540": {"type": "CB 전환",    "safe": False,
               "comment": "에코프로비엠 전환사채 물량 상존. 수급 급변 시 우선 점검."},
    "028300": {"type": "유상증자",   "safe": False,
               "comment": "HLB 유상증자 후 물량 부담 잔존. 임상 이벤트로 상쇄 가능."},
    "196170": {"type": "BW 잔액",   "safe": True,
               "comment": "알테오젠 BW 잔액 존재. 기술수출 모멘텀으로 상쇄 기대."},
    "035720": {"type": "블록딜",     "safe": False,
               "comment": "카카오 주요 주주 블록딜 전례. 추가 블록딜 리스크 모니터링."},
}

NEWS_KEYWORDS = ["정부","정책","수주","어닝서프라이즈","어닝 서프라이즈",
                 "신사업","생태계","수혜","수주잔고","실적","깜짝실적"]
SUFFIX   = {"KOSPI": ".KS", "KOSDAQ": ".KQ"}
NAVER_HDR = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Referer": "https://finance.naver.com/",
}


# ───────────────────────────────────────────────────────────────────────────────
# 체급 분류 — 시가총액(억원) + 주가(원) 기반 3단계
# ───────────────────────────────────────────────────────────────────────────────
GRADE_META = {
    "bluechip": ("👑", "대장주", "시총 1조 이상 대형주",  "#7c3aed", "grade-bluechip",
                 "안정성 높음 — 기관·연기금이 선호하는 대형주"),
    "midcap":   ("⚖️", "중형주", "시총 2천억~1조 중견주", "#059669", "grade-midcap",
                 "실적 뒷받침 중견주 — 적정 변동성"),
    "small":    ("🪙", "소형/동전주", "시총 2천억 미만·주가 2천원 미만", "#d97706", "grade-small",
                 "소형주·저가주 — 변동성 크므로 손절선 필수"),
}

def classify_stock_tier(market_cap: float, close_price: float) -> str:
    """
    market_cap  : 시가총액 (억원)
    close_price : 현재가 (원)

    시총 미확인(0/NaN)일 때는 주가로 fallback:
      - 주가 2천원 미만  → 소형 (저가주는 시총 불문 소형)
      - 주가 2천원 이상  → 중형 (보수적 방어 처리)
    """
    try:
        mc = float(market_cap)
    except (TypeError, ValueError):
        mc = 0.0
    if mc <= 0 or (mc != mc):                      # 시총 불명 → 주가로 fallback
        return "small" if close_price < 2_000 else "midcap"
    if mc >= 10_000:                               # 1조원(10,000억) 이상 → 대장주
        return "bluechip"
    if mc < 2_000 or close_price < 2_000:          # 2천억 미만 or 주가 2천원 미만 → 소형
        return "small"
    return "midcap"


# ───────────────────────────────────────────────────────────────────────────────
# 내일 급등 예측 (기대수익률 + 승률)
# ───────────────────────────────────────────────────────────────────────────────
def calc_tomorrow_forecast(score: float, squeeze: bool, pb_score: float,
                            rsi: float, vol_ratio: float,
                            inst_streak: int, news_cnt: int,
                            safepin: bool, grade: str) -> tuple:
    """
    Returns (win_rate: float, exp_return: float)
    win_rate : 35% ~ 72%  (해당 신호 발생 시 다음날 양봉 확률)
    exp_return: 0.0% ~ 6.0% (기대 상승폭)
    """
    # ── 승률 ──
    win_rate = 35.0 + (score / 100) * 34.0     # 35 ~ 69
    if squeeze:      win_rate += 6.0
    if inst_streak >= 3: win_rate += 3.0
    elif inst_streak >= 2: win_rate += 1.5
    if grade == "small":  win_rate -= 5.0       # 소형/동전주 승률 패널티
    win_rate = max(20.0, min(win_rate, 76.0))

    # ── 기대수익률 ──
    er = 0.3
    if squeeze:              er += 2.2
    if pb_score >= 25:       er += 1.8
    elif pb_score >= 15:     er += 1.0
    elif pb_score >= 8:      er += 0.5
    if inst_streak >= 3:     er += 1.4
    elif inst_streak >= 2:   er += 0.7
    if rsi < 35:             er += 0.8
    elif rsi < 45:           er += 0.4
    er += min(news_cnt * 0.3, 1.2)
    if vol_ratio > 150:      er += 0.4
    if safepin:              er += 0.5
    if grade == "small":     er += 0.8    # 소형주는 변동폭 큼 (양날의 검)
    er = round(min(er, 6.5), 2)

    return round(win_rate, 1), er


# ───────────────────────────────────────────────────────────────────────────────
# UI 헬퍼
# ───────────────────────────────────────────────────────────────────────────────
def index_card_html(name: str, value: str, delta_pct: float, delta_abs: float) -> str:
    if delta_pct > 0:    cls, arrow, sign = "up",   "▲", "+"
    elif delta_pct < 0:  cls, arrow, sign = "down", "▼", ""
    else:                cls, arrow, sign = "flat",  "",  ""
    return f"""
    <div class="index-card">
        <div class="index-name">{name}</div>
        <div class="index-value {cls}">{value}</div>
        <div class="index-delta {cls}">{arrow} {sign}{delta_pct:.2f}%
            <span style="font-weight:400;font-size:12px;color:#9ca3af;">
                &nbsp;({sign}{delta_abs:,.2f})
            </span>
        </div>
    </div>"""


def fit_signal_html(score: float) -> str:
    if score >= 75:   return "<span class='signal-buy'>🔴 즉시 매수</span>"
    elif score >= 55: return "<span class='signal-ready'>🟡 매수 준비</span>"
    elif score >= 35: return "<span class='signal-wait'>⚪ 관망</span>"
    return "<span class='signal-stop'>🔵 진입 불가</span>"


def fit_bar_html(score: float) -> str:
    if score >= 75:   bc = "#ef4444"
    elif score >= 55: bc = "#f59e0b"
    elif score >= 35: bc = "#94a3b8"
    else:             bc = "#1d6ce8"
    return (f'<div class="fit-bar-wrap">'
            f'<div class="fit-bar" style="width:{score}%;background:{bc};"></div></div>'
            f'<div style="font-size:12px;font-weight:800;color:{bc};">{score:.1f}점 / 100점</div>')


def chg_color(v: float) -> str:
    if v > 0:   return "#ef4444"
    elif v < 0: return "#1d6ce8"
    return "#9ca3af"


def tier_class(rank: int) -> str:
    if rank == 1:     return "tier1"
    elif rank <= 3:   return "tier2"
    elif rank <= 7:   return "tier3"
    return "tier4"


def stock_card_html(rank: int, r: pd.Series) -> str:
    tc      = tier_class(rank)
    medals  = {1:"🥇", 2:"🥈", 3:"🥉"}
    medal   = medals.get(rank, f"#{rank}")
    price   = int(r["현재가"]) if not pd.isna(r.get("현재가", float("nan"))) else 0
    chg     = float(r["등락률(%)"])
    cc      = chg_color(chg)
    chg_sym = "▲" if chg > 0 else "▼" if chg < 0 else ""
    sign    = "+" if chg > 0 else ""
    fit     = float(r["매수적합도(%)"])

    # 체급
    grade    = r.get("_grade", "midcap")
    gm       = GRADE_META.get(grade, GRADE_META["midcap"])
    g_icon, g_name, g_desc, g_color, g_cls, g_tip = gm
    grade_badge = (f'<span class="grade-badge {g_cls}">'
                   f'{g_icon} {g_name}</span>'
                   f'<div style="font-size:11px;color:#9ca3af;margin-top:3px;">{g_tip}</div>')

    # 내일 예측
    win_rate   = float(r.get("_win_rate",  0))
    exp_return = float(r.get("_exp_return", 0))
    wr_color   = "#16a34a" if win_rate >= 60 else "#f59e0b" if win_rate >= 45 else "#94a3b8"
    er_color   = "#ef4444" if exp_return >= 2 else "#f97316" if exp_return >= 1 else "#94a3b8"

    # 특수 배지
    badges = ""
    if r.get("_squeeze", False):
        badges += "<span class='badge badge-explode'>💥 급등 대기 [공매도 상환]</span>"
    if r.get("_safepin", False):
        badges += "<span class='badge badge-safe'>🛡️ 안전핀 타점 [물량→하방경직]</span>"

    inst_raw = r.get("_기관당일", 0)
    frgn_raw = r.get("_외국인당일", 0)
    inst_txt = f"{inst_raw:+,}" if inst_raw != 0 else "수집중"
    frgn_txt = f"{frgn_raw:+,}" if frgn_raw != 0 else "수집중"

    score_badges = (
        f"<span class='badge badge-inst'>🏦 기관/연기금 {r['기관/연기금']:.0f}점</span>"
        f"<span class='badge badge-short'>💥 공매도상환 {r['숏스퀴즈']:.0f}점</span>"
        f"<span class='badge badge-pb'>📈 최적매수 {r['눌림목']:.1f}점</span>"
        f"<span class='badge badge-news'>📰 미반영호재 {r['뉴스호재']:.0f}점</span>"
    )

    return f"""
    <div class="stock-card {tc}">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:10px;">

            <!-- 왼쪽: 종목 정보 -->
            <div style="flex:1;min-width:220px;">
                <div class="stock-rank">{medal} {rank}위 &nbsp;<span class="stock-sector">{r['섹터']}</span></div>
                <div class="stock-name">{r['종목명']}</div>
                <div>
                    <span class="stock-price" style="color:{cc};">{price:,}원</span>
                    &nbsp;<span style="font-size:15px;font-weight:700;color:{cc};">{chg_sym} {sign}{chg:.2f}%</span>
                </div>
                <div style="margin-top:7px;">{grade_badge}</div>
                <div style="margin-top:6px;">{badges}</div>
                <div style="margin-top:4px;">{score_badges}</div>
            </div>

            <!-- 오른쪽: 신호 + 예측 -->
            <div style="min-width:200px;display:flex;flex-direction:column;gap:8px;align-items:flex-end;">
                <div>{fit_signal_html(fit)}</div>
                {fit_bar_html(fit)}
                <!-- 내일 예측 -->
                <div style="display:flex;gap:8px;margin-top:4px;">
                    <div class="forecast-box">
                        <div class="forecast-rate" style="color:{er_color};">+{exp_return:.1f}%</div>
                        <div class="forecast-label">내일 기대수익률</div>
                    </div>
                    <div class="forecast-box">
                        <div class="forecast-rate" style="color:{wr_color};">{win_rate:.0f}%</div>
                        <div class="forecast-label">양봉 승률</div>
                    </div>
                </div>
                <div style="font-size:11px;color:#9ca3af;">
                    기관 {inst_txt} | 외국인 {frgn_txt}
                </div>
            </div>
        </div>

        <!-- 하단: AI 분석 -->
        <div style="margin-top:12px;padding-top:10px;border-top:1px solid #f1f5f9;
                    font-size:13px;color:#374151;line-height:1.6;">
            💬 <strong>AI 타점 분석:</strong> {r['타점분석']}
        </div>
    </div>"""


# ───────────────────────────────────────────────────────────────────────────────
# 데이터 함수
# ───────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_investor_data_naver(ticker: str) -> list:
    try:
        r = requests.get("https://finance.naver.com/item/frgn.naver",
                         headers=NAVER_HDR, params={"code": ticker}, timeout=8)
        r.encoding = "euc-kr"
        soup   = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table")
        if len(tables) < 4:
            return []

        def _int(s: str) -> int:
            s = s.replace(",","").replace("+","")
            for w in ("상승","하락","보합"): s = s.replace(w,"")
            try:    return int(s)
            except: return 0

        def _float(s: str) -> float:
            try:    return float(s.replace("%","").strip())
            except: return 0.0

        result = []
        for row in tables[3].find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cells) >= 7 and len(cells[0]) == 10 and cells[0][4] == ".":
                result.append({"날짜": cells[0], "기관": _int(cells[5]),
                                "외국인": _int(cells[6]),
                                "보유율": _float(cells[8]) if len(cells) > 8 else 0.0})
                if len(result) >= 5: break
        return result
    except Exception:
        return []


@st.cache_data(ttl=60)
def get_investor_batch(tickers: tuple) -> dict:
    return {t: get_investor_data_naver(t) for t in tickers}


@st.cache_data(ttl=60, show_spinner=False)
def _get_krx_ref_date(ticker: str) -> str:
    """frgn.naver <em class='date'> 에서 KRX 기준일(장마감 기준) 파싱.

    예) '2026.05.06기준(KRX 장마감)' → '2026.05.06'
    확정 데이터 행의 날짜와 비교해 투자자 테이블의 상태 배지를 결정하는 데 사용.
    42대 점수 로직에는 일절 사용하지 않음.
    """
    try:
        import re as _re
        r = requests.get("https://finance.naver.com/item/frgn.naver",
                         headers=NAVER_HDR, params={"code": ticker}, timeout=8)
        r.encoding = "euc-kr"
        soup = BeautifulSoup(r.text, "html.parser")
        for em in soup.find_all("em", class_="date"):
            dates = _re.findall(r"20\d{2}\.\d{2}\.\d{2}", em.get_text())
            if dates:
                return dates[0]
        return ""
    except Exception:
        return ""


# ── 오늘 가격 잠정 행 (sise_day.naver) ──────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def _get_sise_today_price(ticker: str) -> dict | None:
    """sise_day.naver에서 오늘 날짜 행(종가·등락·거래량)을 반환.
    확정 기관 데이터가 없는 당일 잠정 행 구성에 사용."""
    try:
        today_str = datetime.now(KST).strftime("%Y.%m.%d")
        r = requests.get("https://finance.naver.com/item/sise_day.naver",
                         params={"code": ticker}, headers=NAVER_HDR, timeout=8)
        r.encoding = "euc-kr"
        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table")
        if not tables:
            return None
        for row in tables[0].find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cells) >= 7 and cells[0] == today_str:
                def _safe_int(s: str) -> int:
                    try: return int(s.replace(",", "").replace("+", ""))
                    except: return 0
                chg_raw = cells[2]   # 예: "상승33,500" / "하락1,000"
                sign = -1 if "하락" in chg_raw else 1
                for w in ("상승","하락","보합"): chg_raw = chg_raw.replace(w, "")
                return {
                    "날짜": cells[0],
                    "종가": _safe_int(cells[1]),
                    "전일비": sign * _safe_int(chg_raw),
                    "거래량": _safe_int(cells[6]),
                }
        return None
    except Exception:
        return None


def _investor_html_table(inv_data: list, ticker: str) -> str:
    """기관·외국인 수급 HTML 테이블.

    - 오늘이 거래일인데 확정 데이터가 없으면 sise_day.naver에서 당일 가격을
      가져와 '⏳ 잠정' 행을 최상단에 자동 삽입 (표시 전용; 42대 점수 무영향).
    - 확정 데이터 행은 기관/외국인 색상(🔴상승 🔵하락)으로 코딩.
    """
    now_kst   = datetime.now(KST)
    today_str = now_kst.strftime("%Y.%m.%d")
    today_d   = now_kst.date()
    is_td     = today_d.weekday() < 5 and not _is_krx_holiday(today_d)
    market_open = now_kst.hour >= 9

    confirmed_date = inv_data[0]["날짜"] if inv_data else "—"
    need_provisional = (
        is_td and market_open
        and (not inv_data or inv_data[0]["날짜"] != today_str)
    )

    def _sign_html(v: int) -> str:
        if v > 0: return f'<span style="color:#ef4444;font-weight:700;">+{v:,}</span>'
        if v < 0: return f'<span style="color:#1d6ce8;font-weight:700;">{v:,}</span>'
        return f'<span style="color:#6b7280;">0</span>'

    rows_html = ""

    # ── KRX 기준일 파싱 (frgn.naver em.date) ─────────────────────────────────
    # 예: "2026.05.06 기준(KRX 장마감)" → '2026.05.06'
    # 확정 데이터 날짜(confirmed_date)와 비교해 상태를 정확히 결정
    krx_ref_date = _get_krx_ref_date(ticker)

    # ── 잠정 행 (오늘이 거래일이나 확정 데이터 미발표) ───────────────────────
    if need_provisional:
        after_close = now_kst.hour > 15 or (now_kst.hour == 15 and now_kst.minute >= 30)

        # KRX 기준일이 오늘이면 → 가집계 발표는 됐지만 frgn.naver 미반영 상태
        # KRX 기준일이 오늘이 아니면 → 아직 장이 진행 중이거나 데이터 집계 전
        krx_matches_today = (krx_ref_date == today_str)

        if after_close and krx_matches_today:
            # 장 마감 후, KRX 기준일=오늘: 가집계 완료됐으나 frgn.naver D+1 반영 대기
            badge_txt   = "가집계완료·확정대기"
            badge_bg    = "#fef3c7"
            badge_color = "#92400e"
            inst_cell   = '<td style="padding:7px 10px;color:#92400e;font-size:12px;text-align:right;">가집계완료 (D+1 반영)</td>'
            frgn_cell   = '<td style="padding:7px 10px;color:#92400e;font-size:12px;text-align:right;">가집계완료 (D+1 반영)</td>'
        elif after_close:
            # 장 마감 후, KRX 기준일 미확인: 가집계 발표 예정 / 대기
            badge_txt   = "가집계대기"
            badge_bg    = "#fef3c7"
            badge_color = "#b45309"
            inst_cell   = '<td style="padding:7px 10px;color:#9ca3af;font-size:12px;text-align:right;">가집계 발표 대기</td>'
            frgn_cell   = '<td style="padding:7px 10px;color:#9ca3af;font-size:12px;text-align:right;">가집계 발표 대기</td>'
        else:
            # 장 중
            badge_txt   = "장중"
            badge_bg    = "#dbeafe"
            badge_color = "#1d4ed8"
            inst_cell   = '<td style="padding:7px 10px;color:#9ca3af;font-size:12px;text-align:right;">장중 (미집계)</td>'
            frgn_cell   = '<td style="padding:7px 10px;color:#9ca3af;font-size:12px;text-align:right;">장중 (미집계)</td>'

        price_row = _get_sise_today_price(ticker)
        if price_row:
            chg_v     = price_row["전일비"]
            chg_color = "#ef4444" if chg_v >= 0 else "#1d6ce8"
            price_td  = (
                f'<td style="padding:7px 10px;font-size:12px;color:{chg_color};text-align:right;">'
                f'{price_row["종가"]:,}원 ({chg_v:+,})</td>'
                f'<td style="padding:7px 10px;font-size:11px;color:#6b7280;text-align:right;">'
                f'{price_row["거래량"]:,}주</td>'
            )
        else:
            price_td = '<td colspan="2" style="padding:7px 10px;color:#9ca3af;font-size:11px;">가격 로딩 중…</td>'

        rows_html += f"""
<tr style="background:#fffbeb;border-left:3px solid #f59e0b;">
  <td style="padding:7px 10px;font-weight:700;">
    {today_str}
    <span style="font-size:10px;background:{badge_bg};color:{badge_color};
                 padding:1px 6px;border-radius:10px;margin-left:4px;">{badge_txt}</span>
  </td>
  {inst_cell}
  {frgn_cell}
  {price_td}
</tr>"""

    # ── 확정 행 ───────────────────────────────────────────────────────────────
    for d in inv_data:
        is_latest  = (d["날짜"] == confirmed_date)
        row_bg    = "#fafafa" if is_latest else "#ffffff"
        date_val  = d["날짜"]
        inst_html = _sign_html(d["기관"])
        frgn_html = _sign_html(d["외국인"])
        hold_str  = f'{d["보유율"]:.2f}%'
        status    = "✅ KRX확정 (최신)" if is_latest else "✅ KRX확정"
        rows_html += (
            f'<tr style="background:{row_bg};border-bottom:1px solid #f1f5f9;">'
            f'<td style="padding:7px 10px;color:#000000;">{date_val}</td>'
            f'<td style="padding:7px 10px;text-align:right;">{inst_html}</td>'
            f'<td style="padding:7px 10px;text-align:right;">{frgn_html}</td>'
            f'<td style="padding:7px 10px;text-align:right;color:#374151;">{hold_str}</td>'
            f'<td style="padding:7px 10px;text-align:right;color:#16a34a;font-size:11px;">{status}</td>'
            f'</tr>'
        )

    # ── 하단 주석 ─────────────────────────────────────────────────────────────
    krx_ref_display = f"KRX 기준: <strong>{krx_ref_date}</strong>" if krx_ref_date else ""
    if need_provisional:
        note_extra = (
            f" | {krx_ref_display}" if krx_ref_display else ""
        ) + (
            " | 기관·외국인 가집계는 KRX 공식 포털(data.krx.co.kr) 로그인 후 조회 가능 — "
            "네이버금융 확정치는 익일 09:00 이후 자동 반영"
        )
    else:
        note_extra = f" | {krx_ref_display}" if krx_ref_display else ""

    note = (
        f'<div style="font-size:11px;color:#9ca3af;margin-top:4px;padding:0 4px;line-height:1.6;">'
        f'※ 소스: 네이버금융 frgn.naver (기관합계 = 연기금 포함) '
        f'| KRX 확정 최신일: <strong>{confirmed_date}</strong>'
        f'{note_extra}'
        f'</div>'
    )

    th = '<th style="padding:6px 10px;text-align:{a};background:#f8fafc;font-size:12px;">{t}</th>'
    def _th(t, a="right"): return th.format(a=a, t=t)

    if need_provisional:
        col_headers = (
            _th("날짜", "left") + _th("기관 순매수(주)") + _th("외국인 순매수(주)") +
            _th("오늘 종가/등락") + _th("거래량")
        )
    else:
        col_headers = (
            _th("날짜", "left") + _th("기관 순매수(주)") + _th("외국인 순매수(주)") +
            _th("외국인 보유율") + _th("상태")
        )

    return (
        f'<div style="overflow-x:auto;border-radius:8px;border:1px solid #e2e8f0;">'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px;">'
        f'<thead><tr>{col_headers}</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table></div>{note}'
    )


@st.cache_data(ttl=600)
def get_naver_news(ticker: str) -> list:
    """뉴스 최대 30건 수집 (종목명 필터링은 호출 측에서 수행)."""
    try:
        r = requests.get(
            f"https://finance.naver.com/item/news_news.naver?code={ticker}&page=1",
            headers=NAVER_HDR, timeout=6)
        r.encoding = "euc-kr"
        soup = BeautifulSoup(r.text, "html.parser")
        out = []
        for row in soup.select("table.type5 tr"):
            t_el = row.select_one("td.title a")
            d_el = row.select_one("td.date")
            if t_el and d_el:
                title = t_el.get_text(strip=True)
                if title:
                    out.append(f"[{d_el.get_text(strip=True)}] {title}")
        return out[:30]
    except Exception:
        return []


def filter_news_by_name(headlines: list, stock_name: str) -> list:
    """종목명이 제목에 포함된 뉴스만 반환. 종목명이 없으면 전체 반환."""
    if not stock_name:
        return headlines
    # 2글자 이상 종목명 단어 단위로 분리해 부분 매칭 (예: '삼성전자' or '삼성')
    name_variants = [stock_name]
    if len(stock_name) > 3:
        name_variants.append(stock_name[:3])  # 앞 3글자 약칭도 허용
    return [h for h in headlines
            if any(v in h for v in name_variants)]


@st.cache_data(ttl=600)
def get_news_batch(tickers: tuple) -> dict:
    return {t: get_naver_news(t) for t in tickers}


@st.cache_data(ttl=600)
def fetch_naver_market_list(market: str, max_pages: int = 15) -> pd.DataFrame:
    """Naver 시가총액 랭킹 페이지에서 전종목 기본 시세 일괄 수집 (병렬 HTTP)
    컬럼 확인(실측): td[2]=현재가 | td[4]=등락률(%) | td[6]=시가총액(억원)
                     td[7]=거래대금(백만원→/100=억) | td[8]=외국인비율 | td[9]=거래량
    market: 'KOSPI'(sosok=0) or 'KOSDAQ'(sosok=1)
    """
    sosok = 0 if market == "KOSPI" else 1

    # 총 페이지 수 파악 (첫 페이지 호출 겸용)
    try:
        r0 = requests.get(
            f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={sosok}&page=1",
            headers=NAVER_HDR, timeout=10,
        )
        r0.encoding = "euc-kr"
        soup0 = BeautifulSoup(r0.text, "html.parser")
        pager = soup0.select_one("td.pgRR a")
        total = int(re.search(r"page=(\d+)", pager["href"]).group(1)) if pager else 1
        total = min(total, max_pages)
    except Exception:
        total = max_pages

    def _parse_page(page: int) -> list:
        try:
            r = requests.get(
                f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={sosok}&page={page}",
                headers=NAVER_HDR, timeout=10,
            )
            r.encoding = "euc-kr"
            soup = BeautifulSoup(r.text, "html.parser")
            out = []
            for tr in soup.select("table.type_2 tr[onmouseover]"):
                tds = tr.find_all("td")
                if len(tds) < 10:
                    continue
                a = tds[1].find("a")
                if not a:
                    continue
                m = re.search(r"code=(\d{6})", a.get("href", ""))
                if not m:
                    continue
                ticker = m.group(1)
                name   = a.get_text(strip=True)

                def _f(i: int) -> float:
                    try:
                        return float(
                            tds[i].get_text(strip=True)
                            .replace(",", "").replace("+", "").replace("%", "")
                        )
                    except Exception:
                        return 0.0

                price = _f(2)
                chg   = _f(4)   # 등락률(%)
                mcap  = _f(6)   # 시가총액(억원) — 이미 억원 단위
                amt   = _f(7)   # 거래대금(백만원) → /100 = 억원
                if price <= 0:
                    continue
                out.append({
                    "ticker":       ticker,
                    "종목명":       name,
                    "현재가":       price,
                    "등락률(%)":    chg,
                    "시가총액(억)": mcap,
                    "거래대금(억)": round(amt / 100, 1),
                })
            return out
        except Exception:
            return []

    all_rows: list = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        for rows in ex.map(_parse_page, range(1, total + 1)):
            all_rows.extend(rows)

    if not all_rows:
        return pd.DataFrame()
    df = pd.DataFrame(all_rows).dropna(subset=["ticker"]).set_index("ticker")
    return df[df["거래대금(억)"] >= 0]


def fetch_naver_stock_realtime(ticker: str) -> dict:
    """Naver 모바일 JSON API로 단일 종목 장중 실시간 현재가·등락률·시가총액·거래대금 수집
    엔드포인트: m.stock.naver.com/api/stock/{code}/basic (suffix 불필요, 6자리 코드만)
    반환: {"현재가": int, "등락률": float, "시가총액": float(억), "거래대금": float(억)} or {}
    """
    try:
        url = f"https://m.stock.naver.com/api/stock/{ticker}/basic"
        r = requests.get(url, headers=NAVER_HDR, timeout=5)
        if r.status_code != 200:
            return {}
        d = r.json()
        def _clean_num(val) -> float:
            if val is None:
                return 0.0
            return float(str(val).replace(",", "").replace("%", "").strip() or 0)
        price   = int(_clean_num(d.get("closePrice", 0)))
        chg_pct = _clean_num(d.get("fluctuationsRatio", 0))
        # accumulatedTradingValue 는 원 단위
        trade_val_won = _clean_num(d.get("accumulatedTradingValue", 0))
        trade_val_eok = round(trade_val_won / 1e8, 1)
        # marketValue 는 억원 단위
        mcap_eok = round(_clean_num(d.get("marketValue", 0)), 0)
        if price <= 0:
            return {}
        return {
            "현재가":    price,
            "등락률":    chg_pct,
            "시가총액":  mcap_eok,
            "거래대금":  trade_val_eok,
        }
    except Exception:
        return {}


# ── 뉴스 분류 키워드 ──────────────────────────────────────────────────────────
_GOOD_KW = [
    "수주","계약체결","계약","임상성공","기술수출","어닝서프라이즈","흑자전환","흑자",
    "신사업","투자유치","특허","수혜","정책수혜","매출증가","수출","배당증가",
    "자사주매입","자사주","깜짝실적","실적개선","신고가","급등","호실적","수주잔고",
    "영업이익","순이익 증가","매출 증가","증익","회복","반등","상향","목표가 상향",
]
_BAD_KW = [
    "적자","손실","소송","제재","횡령","배임","부도","파산","리콜","감소",
    "취소","지연","하락","전환사채","유상증자","오버행","조사착수","피소",
    "징계","과태료","하향","경고","불공정","압수수색","혐의","기소",
    "실적 부진","영업손실","매출 감소","구조조정","대량해고","파업",
]
# 미반영 호재 판단 키워드: 호재 키워드와 동시에 존재 시 → 미반영 호재
_UNREF_KW = [
    "깜짝","서프라이즈","어닝서프라이즈","예상 외","예상밖","예상보다","처음",
    "신규","전격","돌발","긴급","당일","首","첫","사상 최초","사상최초",
    "목표가 상향","전망 상향","상향 조정","기대감","미반영","잠재","가능성",
    "향후","내년","중장기","모멘텀","촉매","호재 예상","상승 여력",
]

def classify_news_item(headline: str) -> tuple:
    """Returns ('미반영 호재'|'호재'|'악재'|'중립', matched_keywords)"""
    g = [kw for kw in _GOOD_KW  if kw in headline]
    b = [kw for kw in _BAD_KW   if kw in headline]
    u = [kw for kw in _UNREF_KW if kw in headline]

    # 악재가 호재보다 많으면 악재로 확정
    if b and len(b) >= len(g):
        return "악재", b[:3]
    # 호재 + 미반영 키워드 동시 → 미반영 호재
    if g and u:
        return "미반영 호재", (g[:2] + u[:1])
    # 호재만
    if g:
        return "호재", g[:3]
    # 악재만 (호재가 없는 경우)
    if b:
        return "악재", b[:3]
    return "중립", []


@st.cache_data(ttl=60)
def sniper_price(ticker: str, suffix: str, date_str: str) -> dict:
    """단일 종목 가격·기술분석 데이터
    ① yfinance 60d OHLCV → RSI·눌림목·이동평균 계산 (역사 데이터)
    ② Naver 모바일 API   → 현재가·등락률·거래대금·시가총액 실시간 덮어쓰기
    period='60d' 사용 → 주말·공휴일 직후에도 최근 실제 거래일 자동 선택
    ttl=60 → 1분 캐시 (장중 실시간성 확보)"""
    raw = yf.download(
        ticker + suffix,
        period="60d",
        auto_adjust=True, progress=False,
    )
    if raw.empty:
        return {}
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    if "Close" not in raw.columns:
        return {}
    close  = raw["Close"].dropna()
    volume = raw["Volume"].dropna()
    if len(close) < 11:
        return {}
    cur_yf = float(close.iloc[-1])
    prev   = float(close.iloc[-2])
    vol    = float(volume.iloc[-1])
    avg20  = float(volume.tail(20).mean())
    pb     = calc_pullback_score(close, volume)
    ma5    = float(close.rolling(5).mean().iloc[-1])
    ma10   = float(close.rolling(10).mean().iloc[-1])
    ma20_  = float(close.rolling(20).mean().iloc[-1])

    # ── ② Naver 실시간 덮어쓰기 ─────────────────────────────────────────────
    nv = fetch_naver_stock_realtime(ticker)
    cur       = nv["현재가"]   if nv.get("현재가",   0) > 0 else round(cur_yf)
    chg_pct   = nv["등락률"]   if nv                         else round((cur_yf - prev) / prev * 100, 2)
    trade_eok = nv["거래대금"] if nv.get("거래대금", 0) > 0 else round(cur_yf * vol / 1e8, 1)
    mcap      = nv["시가총액"] if nv.get("시가총액", 0) > 0 else 0.0

    # 수집 시각 (KST, 초 단위)
    collected_at = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

    return {
        "현재가":      cur,
        "등락률":      chg_pct,
        "거래량비율":  round(vol / avg20 * 100, 1),
        "거래대금":    trade_eok,
        "눌림목점수":  pb["score"],
        "눌림목신호":  pb["signal"],
        "RSI":         pb["rsi"],
        "ma5":         round(ma5),
        "ma10":        round(ma10),
        "ma20":        round(ma20_),
        "시가총액":    mcap,
        "수집시각":    collected_at,
        "_naver_ok":   bool(nv),
    }


def calc_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff().dropna()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta).clip(lower=0).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    rsi   = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not rsi.empty else 50.0


def calc_pullback_score(close_s: pd.Series, vol_s: pd.Series) -> dict:
    if len(close_s) < 22:
        return {"score": 0, "signal": "데이터 부족", "rsi": 50}
    ma5  = close_s.rolling(5).mean()
    ma10 = close_s.rolling(10).mean()
    ma20 = close_s.rolling(20).mean()
    cur, prev = float(close_s.iloc[-1]), float(close_s.iloc[-2])
    ma5c  = float(ma5.iloc[-1]);  ma5p = float(ma5.iloc[-2])
    ma10c = float(ma10.iloc[-1])
    ma20c = float(ma20.iloc[-1])
    rsi   = calc_rsi(close_s)
    score = 0

    ma5_gap = (cur - ma5c) / ma5c * 100
    if 0 <= ma5_gap <= 3:    score += 25
    elif -1.5 <= ma5_gap < 0: score += 20

    ma10_gap = (cur - ma10c) / ma10c * 100
    if 0 <= ma10_gap <= 5:   score += 20
    elif -2 <= ma10_gap < 0: score += 15

    if ma5c > ma10c > ma20c:  score += 15
    elif ma5c > ma10c:         score += 8

    price_chg = (cur - prev) / prev * 100
    if price_chg > 0 and prev < ma5p: score += 20
    elif price_chg > 0:                score += 10

    if 30 <= rsi <= 50:   score += 20
    elif 50 < rsi <= 65:  score += 10
    elif rsi < 30:        score += 5

    score = min(score, 100)
    if score >= 75:   sig = "🔴 즉시 매수 (HIGH)"
    elif score >= 50: sig = "🟡 매수 준비 (MID)"
    elif score >= 30: sig = "⚪ 관망 (LOW)"
    else:             sig = "❌ 진입 불가"
    return {"score": score, "signal": sig, "rsi": round(rsi, 1)}


@st.cache_data(ttl=300)
def get_price_data(date_str: str, market: str) -> tuple:
    """전종목 파이프라인 v3.1
    ① Naver 시가총액 랭킹 전종목 스냅샷 (병렬) → 실시간 현재가·등락률·거래대금·시가총액
    ② 거래대금 상위 300 + 소형/저가주 추가 100 선별 → yfinance 일괄 60d OHLCV
    ③ RSI·눌림목 계산
    ④ Naver 실시간값(현재가·등락률·거래대금)으로 yfinance 전일종가 기반값 완전 덮어쓰기
    date_str은 캐시 키 전용; 실다운로드는 항상 최신 60거래일 기준
    반환: (df, actual_date, collection_time_kst)"""
    suffix       = SUFFIX[market]
    known_stocks = {**KOSPI_STOCKS, **KOSDAQ_STOCKS}

    # ── ① Naver 전종목 스냅샷 ──────────────────────────────────────────────────
    snapshot = fetch_naver_market_list(market, max_pages=15)
    if snapshot.empty:
        # Naver 장애 시 기존 정적 DB fallback
        snapshot     = None
        dl_tickers   = list((KOSPI_STOCKS if market == "KOSPI" else KOSDAQ_STOCKS).keys())
    else:
        filtered   = snapshot[snapshot["거래대금(억)"] >= 0.5]
        top_val    = filtered.nlargest(300, "거래대금(억)")           # 유동성 상위 300
        top_small  = filtered[
            (filtered["현재가"] < 5_000) | (filtered["시가총액(억)"] < 2_000)
        ].nlargest(100, "거래대금(억)")                                # 소형·저가 추가 100
        dl_tickers = list(pd.concat([top_val, top_small]).drop_duplicates().index)

    # ── ② yfinance 60d OHLCV 일괄 다운로드 ───────────────────────────────────
    raw = yf.download(
        [t + suffix for t in dl_tickers],
        period="60d",
        auto_adjust=True, progress=False,
    )
    if raw.empty or "Close" not in raw:
        return pd.DataFrame(), None
    close  = raw["Close"].dropna(how="all")
    volume = raw["Volume"].dropna(how="all")
    if len(close) < 11:
        return pd.DataFrame(), None

    actual_date  = close.index[-1].strftime("%Y-%m-%d")
    latest_close = close.iloc[-1]
    prev_close   = close.iloc[-2]
    latest_vol   = volume.iloc[-1]
    avg_vol_20   = volume.tail(20).mean()

    change_pct    = ((latest_close - prev_close) / prev_close * 100).round(2)
    trading_value = (latest_close * latest_vol / 1e8).round(1)
    vol_ratio     = (latest_vol / avg_vol_20 * 100).round(1)

    pb_scores, pb_signals, rsi_vals = [], [], []
    for col in close.columns:
        try:
            pb = calc_pullback_score(close[col].dropna(), volume[col].dropna())
            pb_scores.append(pb["score"]); pb_signals.append(pb["signal"]); rsi_vals.append(pb["rsi"])
        except Exception:
            pb_scores.append(0); pb_signals.append("N/A"); rsi_vals.append(50)

    df = pd.DataFrame({
        "현재가":        latest_close.round(0).astype("Int64"),
        "등락률(%)":     change_pct,
        "거래대금(억)":  trading_value,
        "거래량비율(%)": vol_ratio,
    })
    df.index = [c.replace(suffix, "") for c in df.index]

    # ── ③ 종목명·섹터·시가총액 병합 (Naver 스냅샷 우선, 정적 DB fallback) ──────
    df.insert(0, "종목명", [
        (snapshot.loc[t, "종목명"] if (snapshot is not None and t in snapshot.index)
         else known_stocks[t][0] if t in known_stocks else t)
        for t in df.index
    ])
    df.insert(1, "섹터", [
        known_stocks[t][1] if t in known_stocks else "기타"
        for t in df.index
    ])
    df["눌림목점수"] = pb_scores
    df["눌림목신호"] = pb_signals
    df["RSI"]        = rsi_vals
    df["시가총액(억)"] = [
        float(snapshot.loc[t, "시가총액(억)"]) if (snapshot is not None and t in snapshot.index)
        else 0.0
        for t in df.index
    ]

    # ── ④ Naver 실시간값으로 yfinance 전일종가 기반값 완전 덮어쓰기 ──────────
    # 현재가·등락률·거래대금 은 Naver 스냅샷(장중 누적) 값이 훨씬 정확함
    if snapshot is not None:
        snap_rt = snapshot[["현재가", "등락률(%)", "거래대금(억)"]].reindex(df.index)
        # 유효한 Naver 값만 덮어쓰기 (0·NaN 은 yfinance 값 유지)
        mask_price = snap_rt["현재가"].notna() & (snap_rt["현재가"] > 0)
        mask_amt   = snap_rt["거래대금(억)"].notna() & (snap_rt["거래대금(억)"] > 0)
        df.loc[mask_price, "현재가"]      = snap_rt.loc[mask_price, "현재가"].astype("Int64")
        df.loc[mask_price, "등락률(%)"]   = snap_rt.loc[mask_price, "등락률(%)"]
        df.loc[mask_amt,   "거래대금(억)"] = snap_rt.loc[mask_amt,   "거래대금(억)"]

    # 수집 시각 (KST 초 단위) — cache 저장 시점 = 실제 Naver 데이터 수집 시점
    collection_time = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")

    return (
        df.dropna(subset=["현재가", "거래대금(억)"]).query("`거래대금(억)` > 0"),
        actual_date,
        collection_time,
    )


def score_ticker(ticker: str, row: pd.Series, investor_map: dict, news_map: dict) -> dict:
    data = investor_map.get(ticker, [])
    labels = []
    squeeze_flag = safepin_flag = False
    inst_d0 = foreign_d0 = inst_streak = 0

    # Filter 1: 기관/연기금 (0~30)
    inst_score = 0
    if data:
        d0 = data[0]; inst_d0 = d0["기관"]; foreign_d0 = d0["외국인"]
        if inst_d0 > 0:    inst_score += 8;  labels.append("기관매집")
        if foreign_d0 > 0: inst_score += 7;  labels.append("외국인매집")
        if inst_d0 > 0 and foreign_d0 > 0:
            inst_score += 5; labels.append("🔥쌍끌이")
        inst_streak = sum(1 for d in data[:3] if d["기관"] > 0)
        if inst_streak >= 3:   inst_score += 10; labels.append("💎기관3일연속(연기금포함)")
        elif inst_streak == 2: inst_score += 5;  labels.append("기관2일연속")
    inst_score = min(inst_score, 30)

    # Filter 2: 공매도상환/숏스퀴즈 (0~20)
    short_score = 0
    if len(data) >= 2:
        rf = [d["외국인"] for d in data[:3]]
        ri = [d["기관"]   for d in data[:3]]
        rh = [d["보유율"] for d in data[:3]]
        if rf[0] > 0 and any(f < 0 for f in rf[1:3]):
            short_score += 15; squeeze_flag = True; labels.append("💥외국인매수전환(공매도상환추정)")
        elif rf[0] < 0 and ri[0] > 0:
            short_score += 10; labels.append("기관방어→하방경직")
        elif len(rf) >= 3 and all(f > 0 for f in rf[:3]):
            short_score += 5;  labels.append("외국인3일연속매수")
        if len(rh) >= 2 and rh[0] > rh[1]:
            short_score = min(short_score + 5, 20)
            if "💥" not in " ".join(labels): labels.append("외국인보유율↑")
    short_score = min(short_score, 20)

    # Filter 3: 눌림목 (0~30)
    pb_score = round(float(row.get("눌림목점수", 0)) * 0.30, 1)
    if ticker in OVERHANG_DB and OVERHANG_DB[ticker]["safe"] and pb_score >= 9:
        pb_score = min(pb_score + 5, 30); safepin_flag = True; labels.append("🛡️안전핀타점")
    pb_score = min(pb_score, 30)

    # Filter 4: 뉴스 호재 (0~20)
    news_hits = []
    news_text = " ".join(news_map.get(ticker, []))
    for kw in NEWS_KEYWORDS:
        if kw in news_text and kw not in news_hits: news_hits.append(kw)
    news_score = min(len(news_hits) * 4, 20)
    if news_hits: labels.append(f"📰호재({','.join(news_hits[:3])})")

    total  = min(inst_score + short_score + pb_score + news_score, 100)
    pb_sig = row.get("눌림목신호", "")
    rsi_v  = float(row.get("RSI", 50))
    chg    = float(row.get("등락률(%)", 0))
    vol_r  = float(row.get("거래량비율(%)", 100))

    if "💎기관3일연속(연기금포함)" in labels and "🔥쌍끌이" in labels:
        comment = "기관(연기금 포함)+외국인 쌍끌이 3일 집중 매집 — 즉시 진입 유효"
    elif "💎기관3일연속(연기금포함)" in labels:
        comment = "기관(연기금 포함) 3일 연속 순매수 — 공적 자금 하방 지지, 매집 강력"
    elif squeeze_flag and "🔴 즉시 매수" in pb_sig:
        comment = f"외국인 매수 전환(공매도 상환 추정) + {pb_sig} — 반등 폭발 타이밍"
    elif squeeze_flag:
        comment = "외국인 매도→매수 전환 포착 — 공매도 상환 시 급등 대기"
    elif safepin_flag and "🔥쌍끌이" in labels:
        comment = "물량 주의 종목이지만 하방 경직 확인 + 쌍끌이 — 안전핀 타점"
    elif safepin_flag:
        comment = "잠재 물량(오버행) 있으나 하방 경직성 확보 — 안전핀 최적 타점"
    elif news_hits and "🔥쌍끌이" in labels:
        comment = f"정책·실적 호재({','.join(news_hits[:2])}) + 기관/외국인 쌍끌이 — 즉시 선취"
    elif news_hits:
        comment = f"현재가 미반영 호재({','.join(news_hits[:3])}) — 이벤트 드리븐 진입 검토"
    elif "🔴 즉시 매수" in pb_sig and "🔥쌍끌이" in labels:
        comment = f"5/10일선 최적 눌림목 + 쌍끌이 — RSI {rsi_v:.0f} 저점 탈출 최적 타이밍"
    elif "🔴 즉시 매수" in pb_sig:
        comment = f"5/10일선 지지 확인, RSI {rsi_v:.0f} 저점 — 거래량 증가 시 즉시 진입"
    elif vol_r > 200:
        comment = f"거래량 {vol_r:.0f}% 급증 이상 수급 — 세력 개입 의심, 추격 진입 유의"
    elif chg > 0 and "기관매집" in labels:
        comment = f"기관 순매수 + 상승({chg:+.1f}%) — 기관 주도 상승 초기 단계"
    else:
        comment = f"수급 우위, 거래대금 {float(row.get('거래대금(억)', 0)):,.0f}억 — 분할 진입 검토"

    # 체급 분류 — 시가총액(억원) + 현재가 기반
    price = float(row.get("현재가", 0))
    mcap  = float(row.get("시가총액(억)", 0))
    grade = classify_stock_tier(mcap, price)

    # 내일 예측
    win_rate, exp_return = calc_tomorrow_forecast(
        score=total, squeeze=squeeze_flag, pb_score=pb_score,
        rsi=rsi_v, vol_ratio=vol_r, inst_streak=inst_streak,
        news_cnt=len(news_hits), safepin=safepin_flag, grade=grade,
    )

    return {
        "기관/연기금": inst_score, "숏스퀴즈": short_score,
        "눌림목": pb_score,        "뉴스호재": news_score,
        "매수적합도(%)": round(total, 1), "타점분석": comment,
        "폭발후보": squeeze_flag,  "안전핀": safepin_flag,
        "수급신호": " | ".join(labels) if labels else "—",
        "_기관당일": inst_d0, "_외국인당일": foreign_d0, "_기관연속일": inst_streak,
        "_grade": grade, "_win_rate": win_rate, "_exp_return": exp_return,
        "_news_cnt": len(news_hits),
    }


@st.cache_data(ttl=60)
def get_macro_indices() -> dict:
    syms = {"KOSPI":"^KS11","KOSDAQ":"^KQ11","나스닥":"^IXIC","나스닥선물":"NQ=F"}
    out = {}
    for name, sym in syms.items():
        try:
            h = yf.Ticker(sym).history(period="2d", interval="1d")
            if len(h) >= 2:
                p, c = float(h["Close"].iloc[-2]), float(h["Close"].iloc[-1])
                out[name] = {"현재": c, "변동": c - p, "변동률": (c - p) / p * 100}
            elif len(h) == 1:
                out[name] = {"현재": float(h["Close"].iloc[-1]), "변동": 0, "변동률": 0}
            else:
                out[name] = None
        except Exception:
            out[name] = None
    return out


def get_sector_flow(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty: return pd.DataFrame()
    s = df.groupby("섹터")["거래대금(억)"].sum().sort_values(ascending=False).reset_index()
    s.rename(columns={"거래대금(억)": "섹터 거래대금(억)"}, inplace=True)
    s["비중(%)"] = (s["섹터 거래대금(억)"] / s["섹터 거래대금(억)"].sum() * 100).round(1)
    return s


def detect_overhang(tickers: list) -> list:
    return [{"종목코드": t, **OVERHANG_DB[t]} for t in tickers if t in OVERHANG_DB]


def build_ranked(price_df: pd.DataFrame, investor_map: dict, news_map: dict) -> pd.DataFrame:
    """가격 DF + 수급 + 뉴스 → 점수 계산 → 내일 기대수익률 기준 정렬"""
    top15_base    = price_df.sort_values(["거래대금(억)","거래량비율(%)"], ascending=False).head(15)
    scored_rows   = []
    for ticker, row in top15_base.iterrows():
        s = score_ticker(ticker, row, investor_map, news_map)
        scored_rows.append({
            "종목명": row["종목명"],   "섹터": row["섹터"],
            "현재가": row["현재가"],   "등락률(%)": row["등락률(%)"],
            "RSI": row["RSI"],         "눌림목신호": row["눌림목신호"],
            "거래대금(억)": row["거래대금(억)"],
            "기관/연기금": s["기관/연기금"], "숏스퀴즈": s["숏스퀴즈"],
            "눌림목": s["눌림목"],     "뉴스호재": s["뉴스호재"],
            "매수적합도(%)": s["매수적합도(%)"], "타점분석": s["타점분석"],
            "수급신호": s["수급신호"],
            "_squeeze": s["폭발후보"], "_safepin": s["안전핀"],
            "_기관당일": s["_기관당일"], "_외국인당일": s["_외국인당일"],
            "_기관연속일": s["_기관연속일"],
            "_grade": s["_grade"],     "_win_rate": s["_win_rate"],
            "_exp_return": s["_exp_return"],
        })
    ranked = (
        pd.DataFrame(scored_rows, index=top15_base.index)
        .sort_values(["_exp_return","_win_rate","매수적합도(%)"], ascending=False)
        .reset_index()
    )
    ranked.insert(0, "순위", range(1, len(ranked) + 1))
    return ranked


def score_ticker_small(ticker: str, row: pd.Series,
                       investor_map: dict, news_map: dict) -> dict:
    """소형/동전주 전용 점수 엔진 — 세력 기습 쌍끌이 패턴 탐지.
    42대 필살기(기관 실적·연기금 연속매수 등)는 완전 배제.
    핵심: 단기 낙폭 바닥 + RSI 과매도 + 외국인·기관 기습 동시 매수."""
    data       = investor_map.get(ticker, [])
    inst_d0    = data[0]["기관"]    if data           else 0
    foreign_d0 = data[0]["외국인"] if data           else 0
    inst_d1    = data[1]["기관"]    if len(data) > 1 else 0
    foreign_d1 = data[1]["외국인"] if len(data) > 1 else 0

    labels        = []
    squeeze_score = 0
    squeeze_flag  = False

    # ── A. 기습 쌍끌이 감지 (0~40점) ──────────────────────────────────────────
    if inst_d0 > 0 and foreign_d0 > 0:               # 당일 쌍끌이
        squeeze_score += 20
        squeeze_flag   = True
        labels.append("🔥 기습 쌍끌이 D0")
    if inst_d1 > 0 and foreign_d1 > 0 and (inst_d0 > 0 or foreign_d0 > 0):
        squeeze_score += 10                           # 연속 쌍끌이
        labels.append("연속 쌍끌이")
    if len(data) >= 2 and foreign_d0 > 0 and data[1]["외국인"] < 0:
        squeeze_score += 10                           # 외국인 매도→매수 전환
        squeeze_flag   = True
        labels.append("💥 외국인 전환(숏스퀴즈)")
    elif inst_d0 > 0 and foreign_d0 <= 0:
        squeeze_score += 8;  labels.append("기관 단독 기습")
    elif foreign_d0 > 0 and inst_d0 <= 0:
        squeeze_score += 8;  labels.append("외국인 단독 기습")
    squeeze_score = min(squeeze_score, 40)

    # ── B. 단기 낙폭·눌림목 (0~30점) ──────────────────────────────────────────
    pb_score = round(min(float(row.get("눌림목점수", 0)) * 0.30, 30), 1)

    # ── C. RSI 과매도 (0~20점) ────────────────────────────────────────────────
    rsi_v     = float(row.get("RSI", 50))
    rsi_score = 0
    if rsi_v < 25:
        rsi_score = 20; labels.append(f"📉 RSI극단과매도({rsi_v:.0f})")
    elif rsi_v < 30:
        rsi_score = 15; labels.append(f"📉 RSI과매도({rsi_v:.0f})")
    elif rsi_v < 40:
        rsi_score = 8
    elif rsi_v < 50:
        rsi_score = 3

    # ── D. 거래량 폭발 (0~10점) ───────────────────────────────────────────────
    vol_r     = float(row.get("거래량비율(%)", 100))
    vol_score = 0
    if vol_r >= 300:
        vol_score = 10; labels.append(f"🚀 거래량{vol_r:.0f}%폭발")
    elif vol_r >= 200:
        vol_score = 7;  labels.append(f"📈 거래량{vol_r:.0f}%급증")
    elif vol_r >= 150:
        vol_score = 4

    total = min(100, squeeze_score + pb_score + rsi_score + vol_score)

    # ── 뉴스 호재 ─────────────────────────────────────────────────────────────
    news_text  = " ".join(news_map.get(ticker, []))
    news_hits  = list(dict.fromkeys(kw for kw in NEWS_KEYWORDS if kw in news_text))
    news_score = min(len(news_hits) * 4, 20)
    if news_hits: labels.append(f"📰호재({','.join(news_hits[:2])})")

    # ── 동전주 전용 기대수익률·승률 ───────────────────────────────────────────
    if squeeze_flag and rsi_v < 35 and vol_r >= 200:
        win_rate, exp_return = 55.0, 6.0
    elif squeeze_flag and rsi_v < 40:
        win_rate, exp_return = 50.0, 4.5
    elif squeeze_flag:
        win_rate, exp_return = 45.0, 3.5
    elif rsi_v < 30 and vol_r >= 150:
        win_rate, exp_return = 42.0, 3.0
    elif pb_score >= 18 and rsi_v < 45:
        win_rate, exp_return = 40.0, 2.5
    else:
        win_rate, exp_return = 33.0, 1.5
    if news_hits:
        exp_return += 0.5; win_rate += 3.0

    # ── 타점 분석 코멘트 ──────────────────────────────────────────────────────
    chg = float(row.get("등락률(%)", 0))
    if squeeze_flag and vol_r >= 200:
        comment = (f"🔥 세력 기습 쌍끌이 — 외국인 {foreign_d0:+,} / 기관 {inst_d0:+,} "
                   f"| 거래량 {vol_r:.0f}% | RSI {rsi_v:.0f} 바닥 — 내일 급등 경계")
    elif squeeze_flag:
        comment = (f"외국인·기관 동시 진입 포착(외 {foreign_d0:+,} / 기 {inst_d0:+,}) "
                   f"| RSI {rsi_v:.0f} — 단기 급등 대기, 손절선 필수")
    elif rsi_v < 30 and vol_r >= 150:
        comment = (f"RSI {rsi_v:.0f} 극단 과매도 + 거래량 {vol_r:.0f}% 급증 "
                   f"— 저점 세력 매집 의심, 수급 확인 후 진입")
    elif "💥 외국인 전환(숏스퀴즈)" in " ".join(labels):
        comment = (f"외국인 매도→매수 전환(공매도 상환 추정) | 오늘 {chg:+.1f}% "
                   f"— 급등 트리거 가능성, 고위험 주의")
    else:
        comment = (f"낙폭 {pb_score:.0f}점 · RSI {rsi_v:.0f} · 거래량 {vol_r:.0f}% "
                   f"— 추가 쌍끌이 신호 확인 후 진입 고려")

    mcap  = float(row.get("시가총액(억)", 0))
    price = float(row.get("현재가", 0))
    grade = classify_stock_tier(mcap, price)

    return {
        "기관/연기금":   0.0,
        "숏스퀴즈":      float(squeeze_score),
        "눌림목":        pb_score,
        "뉴스호재":      float(news_score),
        "매수적합도(%)": round(total, 1),
        "타점분석":      comment,
        "수급신호":      " | ".join(labels) if labels else "—",
        "폭발후보":      squeeze_flag,
        "안전핀":        False,
        "_기관당일":     inst_d0,
        "_외국인당일":   foreign_d0,
        "_기관연속일":   0,
        "_grade":        grade,
        "_win_rate":     win_rate,
        "_exp_return":   exp_return,
        "_news_cnt":     len(news_hits),
    }


def build_ranked_small(
    price_df: pd.DataFrame,
    investor_map: dict,   # 기존 TOP15 map (재사용 or 보완)
    news_map: dict,
) -> pd.DataFrame:
    """소형/동전주 전용 빌더 — 거래량비율 기준 후보 확장 +
    소형 종목 전용 수급 배치 조회 + score_ticker_small 엔진 적용"""

    # 1. 소형 후보 추출 (거래량비율 높은 순)
    candidates = price_df.sort_values("거래량비율(%)", ascending=False)
    small_pairs = [
        (ticker, row) for ticker, row in candidates.iterrows()
        if classify_stock_tier(
            float(row.get("시가총액(억)", 0)), float(row.get("현재가", 0))
        ) == "small"
    ]
    if not small_pairs:
        return pd.DataFrame()

    # 2. 소형 후보 전용 수급·뉴스 데이터 별도 배치 조회
    small_tickers  = tuple(t for t, _ in small_pairs)
    small_inv_map  = get_investor_batch(small_tickers)
    small_news_map = get_news_batch(small_tickers)

    # 3. 동전주 전용 엔진으로 점수화
    scored_rows, scored_idx = [], []
    for ticker, row in small_pairs:
        s = score_ticker_small(ticker, row, small_inv_map, small_news_map)
        scored_rows.append({
            "종목명": row["종목명"],    "섹터": row["섹터"],
            "현재가": row["현재가"],    "등락률(%)": row["등락률(%)"],
            "RSI": row["RSI"],          "눌림목신호": row["눌림목신호"],
            "거래대금(억)": row["거래대금(억)"],
            "기관/연기금": s["기관/연기금"],  "숏스퀴즈": s["숏스퀴즈"],
            "눌림목": s["눌림목"],      "뉴스호재": s["뉴스호재"],
            "매수적합도(%)": s["매수적합도(%)"], "타점분석": s["타점분석"],
            "수급신호": s["수급신호"],
            "_squeeze": s["폭발후보"],  "_safepin": s["안전핀"],
            "_기관당일": s["_기관당일"], "_외국인당일": s["_외국인당일"],
            "_기관연속일": s["_기관연속일"],
            "_grade": s["_grade"],      "_win_rate": s["_win_rate"],
            "_exp_return": s["_exp_return"],
        })
        scored_idx.append(ticker)

    if not scored_rows:
        return pd.DataFrame()

    ranked = (
        pd.DataFrame(scored_rows, index=scored_idx)
        .sort_values(["_exp_return", "_win_rate", "매수적합도(%)"], ascending=False)
        .reset_index()
    )
    ranked.insert(0, "순위", range(1, len(ranked) + 1))
    return ranked


def render_ranked_cards(ranked: pd.DataFrame):
    """종목 카드 렌더링"""
    for _, r in ranked.iterrows():
        st.html(stock_card_html(int(r["순위"]), r))


# ───────────────────────────────────────────────────────────────────────────────
# 사이드바 — 가장 먼저 실행해야 date_str 이 UI 전체에서 사용 가능
# ───────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.html("""
<div style="font-size:20px;font-weight:900;color:#13131a;padding:8px 0 2px;">🐳 숨비 애널리틱스</div>
<div style="font-size:12px;color:#9ca3af;margin-bottom:14px;">SOOMBI Analytics v3.0</div>
""")
st.sidebar.markdown("---")
st.sidebar.markdown("**📅 분석 기준일**")
target_date = st.sidebar.date_input("기준일", datetime.now() - timedelta(days=1),
                                     label_visibility="collapsed")
date_str = target_date.strftime("%Y%m%d")

st.sidebar.markdown("---")
if st.sidebar.button("⚡ 실시간 수급/현재가 갱신", use_container_width=True, type="primary"):
    st.cache_data.clear()
    st.session_state["analysis_run"] = True
    st.rerun()

if st.sidebar.button("🔄 데이터 새로고침", use_container_width=True):
    if st.session_state.get("analysis_run"):
        st.cache_data.clear(); st.rerun()
    else:
        st.sidebar.info("먼저 분석을 시작하세요.")

auto_refresh = st.sidebar.toggle("자동 새로고침", value=False)
refresh_interval = 60
if auto_refresh:
    refresh_interval = st.sidebar.selectbox("주기", [30,60,120,300],
        format_func=lambda x: f"{x}초" if x < 60 else f"{x//60}분", index=1)
if auto_refresh and st.session_state.get("analysis_run"):
    cnt = st_autorefresh(interval=refresh_interval * 1000, key="autorefresh")
    if cnt > 0: st.cache_data.clear()

st.sidebar.markdown("---")

# ── KRX 시장 상태 뱃지 ──────────────────────────────────────────────────────
_ms = get_krx_market_status()
_bg_map = {
    "open":   ("#f0fdf4", "#16a34a", "#16a34a"),
    "pre":    ("#fffbeb", "#f59e0b", "#d97706"),
    "after":  ("#fff7ed", "#fdba74", "#ea580c"),
    "closed": ("#f8f9fc", "#e5e7eb", "#6b7280"),
}
_bg, _border, _label_color = _bg_map[_ms["status"]]
with st.sidebar:
    _countdown_html = (
        f'<div class="market-status-countdown" style="color:{_label_color};">'
        f'{_ms["countdown_text"]}</div>'
        if _ms["countdown_text"] else ""
    )
    st.html(f"""
<div style="font-size:11px;font-weight:700;color:#8c8c9e;margin-bottom:4px;letter-spacing:.4px;">
  KRX 시장 상태
</div>
<div class="market-status-badge"
     style="background:{_bg};border-color:{_border};">
  <div class="market-status-dot">{_ms["emoji"]}</div>
  <div class="market-status-text">
    <div class="market-status-label" style="color:{_label_color};">{_ms["label"]}</div>
    <div class="market-status-time">현재 KST {_ms["time_kst"]}</div>
    {_countdown_html}
  </div>
</div>
""")

st.sidebar.markdown("---")
with st.sidebar:
    st.html("""
<div style="font-size:12px;color:#9ca3af;line-height:1.9;">
<strong>📌 정렬 기준</strong><br>
내일 기대수익률 → 양봉 승률 → 매수적합도<br><br>
<strong>🐳 숨비(Soombi)란?</strong><br>
제주 해녀의 잠수 기술. 깊이 분석해<br>
급등 종목을 건져 올립니다.
</div>""")

# ───────────────────────────────────────────────────────────────────────────────
# ■ UI — 헤더
# ───────────────────────────────────────────────────────────────────────────────
st.html("""
<div style="display:flex;align-items:center;gap:14px;padding:8px 0 16px;">
    <div style="font-size:36px;">🐳</div>
    <div>
        <div class="soombi-title">숨비 애널리틱스</div>
        <div class="soombi-sub">SOOMBI Analytics v3.0 · KOSPI&KOSDAQ 동시 분석 · 체급 자동 분류 · 내일 급등 예측</div>
    </div>
</div>
""")

# ── 실시간 데이터 수집 시각 배너 ─────────────────────────────────────────────
_ct_kp = st.session_state.get("kospi_collect_time", "")
_ct_kq = st.session_state.get("kosdaq_collect_time", "")
if _ct_kp or _ct_kq:
    _ct_display = _ct_kp or _ct_kq
    _naver_src  = "네이버 금융 실시간 API (장중 현재가·등락률·거래대금)"
    st.html(f"""
<div style="display:flex;align-items:center;gap:10px;background:#f0fdf4;
            border:1px solid #bbf7d0;border-radius:10px;padding:8px 16px;
            margin-bottom:10px;font-size:12px;">
  <span style="font-size:16px;">📡</span>
  <div>
    <span style="font-weight:800;color:#15803d;">실시간 수집 완료</span>
    <span style="color:#374151;margin-left:8px;">데이터 소스: {_naver_src}</span>
    <span style="color:#9ca3af;margin-left:12px;">|</span>
    <span style="font-weight:700;color:#15803d;margin-left:12px;">수집 시각: {_ct_display}</span>
  </div>
</div>""")
else:
    st.html("""
<div style="display:flex;align-items:center;gap:10px;background:#fff7ed;
            border:1px solid #fed7aa;border-radius:10px;padding:8px 16px;
            margin-bottom:10px;font-size:12px;">
  <span style="font-size:16px;">⚡</span>
  <div>
    <span style="font-weight:800;color:#c2410c;">분석 대기 중</span>
    <span style="color:#374151;margin-left:8px;">
      사이드바의 <strong>⚡ 실시간 수급/현재가 갱신</strong> 버튼을 눌러 장중 실시간 데이터를 수집하세요.
    </span>
  </div>
</div>""")

# ── 지수 전광판 — CSS Grid (모바일 강제 2×2, 데스크톱 1×4) ──────────────────
macro = get_macro_indices()

def _idx_cell(key: str) -> str:
    d = macro.get(key)
    if not d:
        return (f'<div class="index-card">'
                f'<div class="index-name">{key}</div>'
                f'<div class="index-value flat">N/A</div></div>')
    cur = d["현재"]
    v   = f"{cur:,.2f}" if cur < 100_000 else f"{cur:,.0f}"
    pct = d["변동률"]; ab = d["변동"]
    cls   = "up" if pct > 0 else "down" if pct < 0 else "flat"
    arrow = "▲" if pct > 0 else "▼" if pct < 0 else ""
    sign  = "+" if pct > 0 else ""
    return (f'<div class="index-card">'
            f'<div class="index-name">{key}</div>'
            f'<div class="index-value {cls}">{v}</div>'
            f'<div class="index-delta {cls}">{arrow} {sign}{pct:.2f}%'
            f' <span style="font-weight:400;font-size:10px;color:#9ca3af;">({sign}{ab:,.2f})</span>'
            f'</div></div>')

st.html(f"""
<style>
  .idx-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-bottom: 8px;
  }}
  @media (max-width: 640px) {{
    .idx-grid {{ grid-template-columns: repeat(2, 1fr); }}
  }}
</style>
<div class="idx-grid">
  {_idx_cell("KOSPI")}
  {_idx_cell("KOSDAQ")}
  {_idx_cell("나스닥")}
  {_idx_cell("나스닥선물")}
</div>""")

# ───────────────────────────────────────────────────────────────────────────────
# ■ 스나이퍼 — 종목 역인덱스 DB
# ───────────────────────────────────────────────────────────────────────────────
_ALL_STKS  = {**KOSPI_STOCKS, **KOSDAQ_STOCKS}
_CODE_MKT  = {**{c: "KOSPI" for c in KOSPI_STOCKS}, **{c: "KOSDAQ" for c in KOSDAQ_STOCKS}}
_NAME_CODE = {v[0]: k for k, v in _ALL_STKS.items()}

def _resolve_sniper(q: str):
    """코드/이름/부분명 검색 → (code, market, name, sector) or None
    정적 DB 92종목 → 동적 price_df (전종목 확장 후 신규 종목) 순서로 탐색"""
    q = q.strip()
    # 1. 정적 DB 코드 직접 조회
    if q in _CODE_MKT:
        code = q; mkt = _CODE_MKT[q]
        name, sector = _ALL_STKS[code]
        return code, mkt, name, sector
    # 2. 정적 DB 이름 조회
    if q in _NAME_CODE:
        code = _NAME_CODE[q]; mkt = _CODE_MKT[code]
        name, sector = _ALL_STKS[code]
        return code, mkt, name, sector
    # 3. 정적 DB 부분 이름 매칭
    for code, (name, sector) in _ALL_STKS.items():
        if q in name:
            return code, _CODE_MKT[code], name, sector
    # 4. 동적 price_df 에서 검색 (전종목 확장 이후 신규 종목 지원)
    if re.match(r"^\d{6}$", q):
        for mkt in ("KOSPI", "KOSDAQ"):
            df_s = st.session_state.get(f"{mkt.lower()}_result")
            if df_s is not None and q in df_s.index:
                return q, mkt, str(df_s.loc[q, "종목명"]), str(df_s.loc[q, "섹터"])
        # 코드는 맞지만 미분석 — KOSPI로 우선 시도 (sniper_price 가 suffix 처리)
        return q, "KOSPI", q, "기타"
    # 5. 동적 price_df 부분 이름 매칭
    for mkt in ("KOSPI", "KOSDAQ"):
        df_s = st.session_state.get(f"{mkt.lower()}_result")
        if df_s is not None and "종목명" in df_s.columns:
            hits = df_s[df_s["종목명"].str.contains(q, na=False)]
            if not hits.empty:
                ticker = hits.index[0]
                return ticker, mkt, str(hits.iloc[0]["종목명"]), str(hits.iloc[0]["섹터"])
    return None, None, None, None

# ───────────────────────────────────────────────────────────────────────────────
# ■ UI — 스나이퍼 검색창
# ───────────────────────────────────────────────────────────────────────────────
st.html("""
<div class="sniper-header">
    <div class="sniper-title">🎯 단일 종목 정밀 스나이퍼</div>
    <div class="sniper-sub">종목명 또는 6자리 코드 입력 → 42대 필살기 로직 100% 가동 · 기관/외국인/눌림목/뉴스 완전 해부 · 호재·악재 자동 분류</div>
</div>""")

_sq_col, _sb_col = st.columns([5, 1])
with _sq_col:
    _sniper_q = st.text_input(
        "sniper_q",
        placeholder="🔍  종목명 또는 코드 입력  (예: 삼성전자 · 005930 · SK하이닉스 · HLB · 에코프로)",
        label_visibility="collapsed",
        key="sniper_input",
    )
with _sb_col:
    _sniper_clicked = st.button("🎯 해부 시작", use_container_width=True, key="sniper_btn")

if _sniper_clicked and _sniper_q:
    _code, _mkt, _name, _sector = _resolve_sniper(_sniper_q)
    if _code:
        st.session_state["sniper_code"]   = _code
        st.session_state["sniper_mkt"]    = _mkt
        st.session_state["sniper_name"]   = _name
        st.session_state["sniper_sector"] = _sector
    else:
        st.error(f"'{_sniper_q}' 종목을 찾을 수 없습니다. 등록된 종목명 또는 6자리 코드를 입력해 주세요.")

# ── 스나이퍼 결과 ──────────────────────────────────────────────────────────────
if "sniper_code" in st.session_state:
    _sc   = st.session_state["sniper_code"]
    _smkt = st.session_state["sniper_mkt"]
    _sn   = st.session_state.get("sniper_name", _sc)
    _ss   = st.session_state.get("sniper_sector", "기타")
    _sfx  = SUFFIX[_smkt]

    with st.spinner(f"🎯 {_sn}({_sc}) 정밀 해부 중 — 4대 필살기 가동…"):
        _sp    = sniper_price(_sc, _sfx, date_str)
        _sinv  = get_investor_data_naver(_sc)
        _snews = get_naver_news(_sc)

    if not _sp:
        st.warning(f"⚠️ {_sn}({_sc}) 가격 데이터를 수집하지 못했습니다. 기준일을 변경해 보세요.")
    else:
        # ── 점수 계산 ────────────────────────────────────────────────────────
        _srow = pd.Series({
            "눌림목점수":    _sp["눌림목점수"],
            "눌림목신호":    _sp["눌림목신호"],
            "RSI":           _sp["RSI"],
            "등락률(%)":     _sp["등락률"],
            "거래량비율(%)": _sp["거래량비율"],
            "거래대금(억)":  _sp["거래대금"],
            "현재가":        _sp["현재가"],
            "시가총액(억)":  _sp.get("시가총액", 0),
        })
        _sscore   = score_ticker(_sc, _srow, {_sc: _sinv}, {_sc: _snews})
        _sc_total = _sscore["매수적합도(%)"]
        _sc_color = ("#ef4444" if _sc_total >= 75 else
                     "#f59e0b" if _sc_total >= 55 else
                     "#94a3b8" if _sc_total >= 35 else "#1d6ce8")
        _price    = _sp["현재가"]
        _chg      = _sp["등락률"]
        _cc       = "#ef4444" if _chg > 0 else "#1d6ce8" if _chg < 0 else "#9ca3af"
        _chg_sym  = "▲" if _chg > 0 else "▼" if _chg < 0 else ""
        _grade    = _sscore["_grade"]
        _gm       = GRADE_META.get(_grade, GRADE_META["midcap"])
        _gbadge   = f'<span class="grade-badge {_gm[4]}">{_gm[0]} {_gm[1]}</span>'
        _wr       = _sscore["_win_rate"]
        _er       = _sscore["_exp_return"]
        _wr_c     = "#16a34a" if _wr >= 60 else "#f59e0b" if _wr >= 45 else "#94a3b8"
        _er_c     = "#ef4444" if _er >= 2  else "#f97316" if _er >= 1  else "#94a3b8"
        _rsi      = _sp["RSI"]
        _vr       = _sp["거래량비율"]
        _ma5, _ma10, _ma20 = _sp["ma5"], _sp["ma10"], _sp["ma20"]
        _ma5_gap  = round((_price - _ma5)  / _ma5  * 100, 1) if _ma5  else 0
        _ma10_gap = round((_price - _ma10) / _ma10 * 100, 1) if _ma10 else 0
        _ma20_gap = round((_price - _ma20) / _ma20 * 100, 1) if _ma20 else 0
        _ma_trend = ("정배열 ✅" if _ma5 > _ma10 > _ma20
                     else "역배열 ⚠️" if _ma5 < _ma10 < _ma20
                     else "혼조 ↔")
        _rsi_color = "#16a34a" if _rsi <= 40 else "#ef4444" if _rsi >= 70 else "#374151"
        _rsi_label = ("과매도↑" if _rsi <= 30 else "저점권" if _rsi <= 45
                      else "과매수↓" if _rsi >= 70 else "정상")
        _vr_color  = "#ef4444" if _vr > 150 else "#374151"
        _vr_label  = "🔥 폭발" if _vr > 300 else "급증" if _vr > 150 else "정상"

        def _gap_color(g):
            return "#16a34a" if -2 <= g <= 5 else "#f97316" if g > 5 else "#ef4444"

        _pb_sig_short = _sp["눌림목신호"][:10] if len(_sp["눌림목신호"]) > 10 else _sp["눌림목신호"]

        # 특수 배지
        _s_badges = ""
        if _sscore.get("폭발후보"):
            _s_badges += "<span class='badge badge-explode'>💥 공매도 상환 감지</span> "
        if _sscore.get("안전핀"):
            _s_badges += "<span class='badge badge-safe'>🛡️ 안전핀 타점</span>"

        # 수집시각 & 데이터소스 배지
        _collected_at = _sp.get("수집시각", "")
        _naver_ok     = _sp.get("_naver_ok", False)
        _src_label    = "📡 네이버 금융 실시간 API" if _naver_ok else "📊 yfinance (전일 종가)"
        _src_color    = "#15803d" if _naver_ok else "#b45309"
        _src_bg       = "#f0fdf4" if _naver_ok else "#fffbeb"
        _src_border   = "#bbf7d0" if _naver_ok else "#fde68a"

        _time_span = (
            f'<span style="color:#9ca3af;margin-left:8px;">수집 시각: '
            f'<strong style="color:{_src_color};">{_collected_at}</strong></span>'
            if _collected_at else ""
        )
        st.html(f"""
<div style="display:flex;align-items:center;gap:10px;background:{_src_bg};
            border:1px solid {_src_border};border-radius:8px;padding:6px 14px;
            margin-bottom:8px;font-size:11px;">
  <span style="font-weight:800;color:{_src_color};">{_src_label}</span>
  {_time_span}
</div>""")

        st.html(f"""
<div class="sniper-card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;margin-bottom:16px;">
    <div>
      <div class="sniper-name">{_sn}</div>
      <div class="sniper-meta">{_sc} · {_smkt} · {_ss}</div>
      <div style="margin:6px 0;">
        <span style="font-size:24px;font-weight:900;color:{_cc};">{_price:,}원</span>
        <span style="font-size:15px;font-weight:700;color:{_cc};margin-left:8px;">{_chg_sym} {_chg:+.2f}%</span>
      </div>
      <div style="margin-bottom:6px;">{_gbadge}</div>
      <div>{_s_badges}</div>
    </div>
    <div style="text-align:center;background:#f8fafc;border-radius:16px;padding:16px 22px;border:2px solid {_sc_color};">
      <div style="font-size:44px;font-weight:900;color:{_sc_color};line-height:1;">{_sc_total:.0f}</div>
      <div style="font-size:11px;color:#9ca3af;margin-top:2px;">매수 적합도 / 100점</div>
      <div style="margin-top:8px;">{fit_signal_html(_sc_total)}</div>
      <div style="margin-top:10px;display:flex;gap:8px;">
        <div style="background:#fff;border-radius:8px;padding:6px 10px;border:1px solid #e2e8f0;text-align:center;">
          <div style="font-size:17px;font-weight:900;color:{_wr_c};">{_wr:.0f}%</div>
          <div style="font-size:10px;color:#9ca3af;">양봉 승률</div>
        </div>
        <div style="background:#fff;border-radius:8px;padding:6px 10px;border:1px solid #e2e8f0;text-align:center;">
          <div style="font-size:17px;font-weight:900;color:{_er_c};">+{_er:.1f}%</div>
          <div style="font-size:10px;color:#9ca3af;">기대수익률</div>
        </div>
      </div>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px;">
    <div class="filter-box">
      <div class="filter-name">🏦 기관/연기금</div>
      <div class="filter-score" style="color:#dc2626;">{_sscore["기관/연기금"]:.0f}</div>
      <div class="filter-max">/ 30점</div>
    </div>
    <div class="filter-box">
      <div class="filter-name">💥 공매도상환</div>
      <div class="filter-score" style="color:#ea580c;">{_sscore["숏스퀴즈"]:.0f}</div>
      <div class="filter-max">/ 20점</div>
    </div>
    <div class="filter-box">
      <div class="filter-name">📈 눌림목</div>
      <div class="filter-score" style="color:#16a34a;">{_sscore["눌림목"]:.1f}</div>
      <div class="filter-max">/ 30점</div>
    </div>
    <div class="filter-box">
      <div class="filter-name">📰 미반영호재</div>
      <div class="filter-score" style="color:#2563eb;">{_sscore["뉴스호재"]:.0f}</div>
      <div class="filter-max">/ 20점</div>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:14px;">
    <div>
      <div style="font-size:13px;font-weight:800;color:#374151;margin-bottom:8px;">📐 이동평균선 분석</div>
      <div class="ma-row">
        <span class="ma-label">5일선</span>
        <span class="ma-val">{_ma5:,}원</span>
        <span style="font-size:12px;font-weight:700;color:{_gap_color(_ma5_gap)};">{_ma5_gap:+.1f}%</span>
      </div>
      <div class="ma-row">
        <span class="ma-label">10일선</span>
        <span class="ma-val">{_ma10:,}원</span>
        <span style="font-size:12px;font-weight:700;color:{_gap_color(_ma10_gap)};">{_ma10_gap:+.1f}%</span>
      </div>
      <div class="ma-row">
        <span class="ma-label">20일선</span>
        <span class="ma-val">{_ma20:,}원</span>
        <span style="font-size:12px;font-weight:700;color:{_gap_color(_ma20_gap)};">{_ma20_gap:+.1f}%</span>
      </div>
      <div style="margin-top:6px;font-size:12px;font-weight:700;color:#6b7280;">배열: {_ma_trend}</div>
    </div>
    <div>
      <div style="font-size:13px;font-weight:800;color:#374151;margin-bottom:8px;">📊 기술 지표</div>
      <div class="ma-row">
        <span class="ma-label">RSI(14)</span>
        <span class="ma-val" style="color:{_rsi_color};">{_rsi:.1f}</span>
        <span style="font-size:11px;color:#9ca3af;">{_rsi_label}</span>
      </div>
      <div class="ma-row">
        <span class="ma-label">거래량</span>
        <span class="ma-val" style="color:{_vr_color};">{_vr:.0f}%</span>
        <span style="font-size:11px;color:#9ca3af;">{_vr_label}</span>
      </div>
      <div class="ma-row">
        <span class="ma-label">눌림목</span>
        <span class="ma-val">{_sp["눌림목점수"]}점</span>
        <span style="font-size:11px;color:#9ca3af;">{_pb_sig_short}</span>
      </div>
      <div class="ma-row">
        <span class="ma-label">거래대금</span>
        <span class="ma-val">{_sp["거래대금"]:,.0f}억</span>
      </div>
    </div>
  </div>

  <div style="margin-top:2px;padding-top:12px;border-top:1px solid #f1f5f9;font-size:13px;color:#374151;line-height:1.7;">
    💬 <strong>AI 타점 분석:</strong> {_sscore["타점분석"]}
  </div>
</div>""")

        # ── 기관·외국인 수급 ─────────────────────────────────────────────────
        # 잠정/확정 이원화 파이프라인: _investor_html_table() 이 오늘 거래일이면
        # sise_day.naver 가격 행을 '장중잠정/마감후집계중' 배지로 자동 삽입한다.
        # 42대 점수 계산엔 _sinv (frgn.naver 확정치) 만 사용 — 골든룰 준수.
        st.html(
            '<div style="font-size:14px;font-weight:800;color:#13131a;'
            'margin:8px 0 4px;">🏦 기관·외국인 수급 흐름</div>'
        )
        st.html(_investor_html_table(_sinv, _sc))

        # ── 뉴스 분류 ────────────────────────────────────────────────────────
        # 1) 종목명 필터링: 해당 종목명이 제목에 포함된 기사만
        _snews_filtered = filter_news_by_name(_snews, _sname)
        _news_src = _snews_filtered if _snews_filtered else _snews  # fallback: 전체
        _filtered_note = (f"({len(_snews_filtered)}/{len(_snews)}건 종목 관련)"
                          if _snews_filtered else f"({len(_snews)}건 전체 — 종목명 매칭 없음)")

        if _news_src:
            st.html(
                f'<div style="font-size:14px;font-weight:800;color:#13131a;margin:12px 0 4px;">'
                f'📰 뉴스 자동 분류 <span style="font-size:11px;font-weight:400;'
                f'color:#6b7280;">{_filtered_note}</span></div>'
            )

            # 2) 3-카테고리 분류 (중립 제외)
            _unref_items = []   # 미반영 호재
            _good_items  = []   # 호재
            _bad_items   = []   # 악재

            for _h in _news_src:
                _cat, _kws = classify_news_item(_h)
                _kw_tag = (f'<span style="font-size:10px;color:#6b7280;margin-left:4px;">'
                           f'[{", ".join(_kws)}]</span>') if _kws else ""
                if _cat == "미반영 호재":
                    _unref_items.append((_h, _kw_tag))
                elif _cat == "호재":
                    _good_items.append((_h, _kw_tag))
                elif _cat == "악재":
                    _bad_items.append((_h, _kw_tag))
                # 중립은 표시 안 함

            # 3) 종합 요약 배너
            _total_sig = len(_unref_items) + len(_good_items) + len(_bad_items)
            if _unref_items:
                _sum_color = "#2563eb"
                _sum_text  = f"🔥 미반영 호재 {len(_unref_items)}건 감지 — 선취매 검토"
            elif len(_good_items) > len(_bad_items):
                _sum_color = "#16a34a"
                _sum_text  = f"호재 {len(_good_items)}건 우세 — 긍정 편향"
            elif len(_bad_items) > len(_good_items):
                _sum_color = "#dc2626"
                _sum_text  = f"악재 {len(_bad_items)}건 우세 — 부정 편향"
            else:
                _sum_color = "#94a3b8"
                _sum_text  = "중립 — 유의미 시그널 없음"

            st.html(
                f'<div style="background:{_sum_color}18;border-radius:10px;padding:9px 14px;'
                f'margin-bottom:8px;border:1px solid {_sum_color}40;font-size:13px;'
                f'font-weight:700;color:{_sum_color};">'
                f'📊 {_sname} 뉴스 종합 (유의미 {_total_sig}건): {_sum_text}</div>'
            )

            # 4) 탭: 미반영 호재 / 호재 / 악재 (비어있는 탭 제외)
            _tab_defs = []
            if _unref_items: _tab_defs.append(("🔥 미반영 호재", _unref_items, "#2563eb", "nc-unref"))
            if _good_items:  _tab_defs.append(("🟢 호재",        _good_items,  "#16a34a", "nc-good"))
            if _bad_items:   _tab_defs.append(("🔴 악재",        _bad_items,   "#dc2626", "nc-bad"))

            if _tab_defs:
                _tab_labels = [f"{td[0]} ({len(td[1])})" for td in _tab_defs]
                _tabs = st.tabs(_tab_labels)
                for _tab_ui, (_label, _items, _color, _cls) in zip(_tabs, _tab_defs):
                    with _tab_ui:
                        _html_block = ""
                        for _h, _kw_tag in _items:
                            _icon = "🔥" if "미반영" in _label else ("🟢" if "호재" in _label else "🔴")
                            _html_block += (
                                f'<div class="{_cls}" style="margin-bottom:6px;padding:8px 10px;'
                                f'border-radius:7px;border-left:3px solid {_color};">'
                                f'{_icon} {_h}{_kw_tag}</div>'
                            )
                        st.html(_html_block)
            else:
                st.info("종목 관련 유의미 뉴스(호재·악재)가 감지되지 않았습니다.")

    # ── 결과 닫기 ──────────────────────────────────────────────────────────────
    if st.button("✕ 스나이퍼 결과 닫기", key="sniper_clear"):
        for _k in ["sniper_code", "sniper_mkt", "sniper_name", "sniper_sector"]:
            st.session_state.pop(_k, None)
        st.rerun()

# ── 장세 코멘트 ───────────────────────────────────────────────────────────────
kd = macro.get("KOSPI"); nd = macro.get("나스닥"); nfd = macro.get("나스닥선물")
lines = []
if kd:
    if kd["변동률"] > 0.5:    lines.append(f"🔴 <strong>국내 강세</strong>: KOSPI {kd['변동률']:+.2f}% — 기관·외국인 순매수 우위. 매수 여건 유리.")
    elif kd["변동률"] < -0.5: lines.append(f"🔵 <strong>국내 약세</strong>: KOSPI {kd['변동률']:+.2f}% — 외국인 이탈 또는 프로그램 매도. 눌림목 진입 검토.")
    else:                      lines.append(f"⚪ <strong>국내 보합</strong>: KOSPI {kd['변동률']:+.2f}% — 관망세. 개별 수급 집중.")
if nd:
    if nd["변동률"] > 0.5:    lines.append(f"🔴 <strong>글로벌 상승</strong>: 나스닥 {nd['변동률']:+.2f}% — 반도체·성장주 수급 유리.")
    elif nd["변동률"] < -0.5: lines.append(f"🔵 <strong>글로벌 하락</strong>: 나스닥 {nd['변동률']:+.2f}% — IT·바이오 수급 압박 주의.")
    else:                      lines.append(f"⚪ <strong>글로벌 보합</strong>: 나스닥 방향성 불명확 — 국내 수급 주도장 예상.")
if nfd:
    sign = "상승" if nfd["변동률"] >= 0 else "하락"
    lines.append(f"📡 <strong>나스닥선물</strong>: {nfd['변동률']:+.2f}% {sign} — 다음 장 개장 분위기 선반영.")
st.html(f"""
<div class="macro-card">
    <div style="font-size:14px;font-weight:800;color:#13131a;margin-bottom:8px;">📊 지금 시장은?</div>
    <div style="font-size:13px;color:#374151;line-height:1.9;">{"<br>".join(lines) or "데이터 수집 중..."}</div>
    <div style="font-size:11px;color:#c4c4cf;margin-top:8px;">
        ※ 한국 증시 기준: 🔴 상승(빨강) | 🔵 하락(파랑)
    </div>
</div>""")

# ── 체급 설명 카드 ────────────────────────────────────────────────────────────
st.html("""
<div class="macro-card">
    <div style="font-size:14px;font-weight:800;color:#13131a;margin-bottom:10px;">
        🏷️ 종목 체급 분류 안내 — 1초 만에 위험도 파악
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:10px;font-size:13px;">
        <div><span class="grade-badge grade-bluechip">👑 대장주</span>
             <span style="color:#6b7280;margin-left:6px;">시총 1조 이상. 기관·연기금 선호. 안정성 높음.</span></div>
        <div><span class="grade-badge grade-midcap">⚖️ 중형주</span>
             <span style="color:#6b7280;margin-left:6px;">시총 2천억~1조 중견주. 실적 뒷받침. 적정 변동성.</span></div>
        <div><span class="grade-badge grade-small">🪙 소형/동전주</span>
             <span style="color:#6b7280;margin-left:6px;">시총 2천억 미만 또는 주가 2천원 미만. 고변동성. 손절선 필수.</span></div>
    </div>
</div>""")

# ───────────────────────────────────────────────────────────────────────────────
# 공통: 분석 실행 (양쪽 시장 동시)
# ───────────────────────────────────────────────────────────────────────────────
if st.session_state.get("analysis_run"):
    with st.spinner("📈 KOSPI · KOSDAQ 주가 데이터 동시 수집 중…"):
        _kp_df, _kp_date, _kp_ctime = get_price_data(date_str, "KOSPI")
        _kq_df, _kq_date, _kq_ctime = get_price_data(date_str, "KOSDAQ")

    if _kp_df is not None and not _kp_df.empty:
        st.session_state["kospi_result"]       = _kp_df
        st.session_state["kospi_date"]         = _kp_date
        st.session_state["kospi_collect_time"] = _kp_ctime
    else:
        st.session_state["kospi_result"] = None

    if _kq_df is not None and not _kq_df.empty:
        st.session_state["kosdaq_result"]       = _kq_df
        st.session_state["kosdaq_date"]         = _kq_date
        st.session_state["kosdaq_collect_time"] = _kq_ctime
    else:
        st.session_state["kosdaq_result"] = None

# ───────────────────────────────────────────────────────────────────────────────
# 탭
# ───────────────────────────────────────────────────────────────────────────────
tab_kp, tab_kq, tab_bc, tab_mc, tab_sm, tab_supply, tab_sector, tab_news, tab_oh = st.tabs([
    "🏆 KOSPI TOP 15",
    "🔷 KOSDAQ TOP 15",
    "👑 대장주",
    "📈 중형주",
    "🪙 소형/동전주",
    "📊 수급 분석표",
    "💰 섹터 돈의 흐름",
    "📰 미반영 뉴스",
    "⚠️ 물량 주의 종목",
])


def _run_btn(key: str, label: str = "🚀 KOSPI · KOSDAQ 동시 분석 시작"):
    if st.button(label, key=key, use_container_width=True):
        st.session_state["analysis_run"] = True
        st.cache_data.clear()


def render_market_tab(market_name: str, result_key: str, date_key: str,
                      run_btn_key: str, market_code: str):
    """KOSPI / KOSDAQ 공통 랭킹 탭 렌더 함수"""
    icon = "🏆" if market_code == "KOSPI" else "🔷"
    st.html(f'<div class="section-header">{icon} {market_name} 내일 급등 예측 TOP 15</div>')
    st.html("""
    <div class="section-sub">
    정렬 기준: <strong>내일 기대수익률</strong> → 양봉 승률 → AI 매수적합도 |
    체급 배지로 위험도 즉시 확인 | 🏦기관/연기금(30pt) + 💥공매도상환(20pt) + 📈최적매수(30pt) + 📰호재(20pt)
    </div>""")

    _run_btn(run_btn_key, f"🚀 {market_name} 분석 시작")
    result = st.session_state.get(result_key)

    if result is not None and not result.empty:
        actual_date = st.session_state.get(date_key, "")
        if actual_date and actual_date != target_date.strftime("%Y-%m-%d"):
            st.info(f"📅 **{actual_date}** 기준 (요청일 데이터 없음 → 최근 거래일 적용)")

        top15_tickers = tuple(result.sort_values(
            ["거래대금(억)","거래량비율(%)"], ascending=False).head(15).index.tolist())

        with st.spinner(f"🏦 {market_name} 기관·외국인 실데이터 수집 중…"):
            investor_map = get_investor_batch(top15_tickers)
        with st.spinner(f"📰 {market_name} 뉴스 호재 분석 중…"):
            news_map = get_news_batch(top15_tickers)

        ranked = build_ranked(result, investor_map, news_map)
        st.session_state[f"{market_code.lower()}_ranked"]       = ranked
        st.session_state[f"{market_code.lower()}_price_df"]     = result
        st.session_state[f"{market_code.lower()}_investor_map"] = investor_map
        st.session_state[f"{market_code.lower()}_news_map"]     = news_map

        # ── 요약 통계 카드 ──────────────────────────────────────────────────
        grade_counts = ranked["_grade"].value_counts()
        g_cols = st.columns(3)
        for col, (gk, gm) in zip(g_cols, GRADE_META.items()):
            cnt = int(grade_counts.get(gk, 0))
            with col:
                st.html(f"""
                <div class="index-card" style="padding:14px 18px;">
                    <div class="index-name">{gm[0]} {gm[1]}</div>
                    <div class="index-value" style="font-size:24px;color:{gm[3]};">{cnt}종목</div>
                    <div style="font-size:11px;color:#9ca3af;">{gm[2]}</div>
                </div>""")

        avg_wr = ranked["_win_rate"].mean()
        avg_er = ranked["_exp_return"].mean()
        top_er = ranked["_exp_return"].max()
        st.html(f"""
        <div class="macro-card" style="margin-top:4px;">
            <div style="display:flex;gap:24px;flex-wrap:wrap;font-size:13px;">
                <div>📊 <strong>평균 양봉 승률</strong>:
                    <span style="color:#16a34a;font-weight:800;">{avg_wr:.1f}%</span></div>
                <div>📈 <strong>평균 기대수익률</strong>:
                    <span style="color:#ef4444;font-weight:800;">+{avg_er:.2f}%</span></div>
                <div>🚀 <strong>최고 기대수익</strong>:
                    <span style="color:#7c3aed;font-weight:800;">+{top_er:.2f}%</span>
                    ({ranked.iloc[0]["종목명"]})</div>
            </div>
        </div>""")

        # ── 종목 카드 ────────────────────────────────────────────────────────
        render_ranked_cards(ranked)

        # ── 실데이터 확인 ────────────────────────────────────────────────────
        with st.expander("🔍 기관·외국인 실데이터 원본 확인 (종목별 잠정/확정 현황)", expanded=False):
            _dbg_today_str = datetime.now(KST).strftime("%Y.%m.%d")
            _dbg_today_d   = datetime.now(KST).date()
            _dbg_is_td     = (_dbg_today_d.weekday() < 5 and not _is_krx_holiday(_dbg_today_d))
            _all_dates     = [investor_map[t][0]["날짜"] for t in top15_tickers if investor_map.get(t)]
            _latest_conf   = max(_all_dates) if _all_dates else "—"
            _need_prov     = (_latest_conf != _dbg_today_str and _dbg_is_td
                              and datetime.now(KST).hour >= 9)

            if _need_prov:
                _ac = datetime.now(KST).hour > 15 or (datetime.now(KST).hour == 15 and datetime.now(KST).minute >= 30)
                _st = "마감 후 집계 중" if _ac else "장중"
                st.html(f"""<div style="background:#dbeafe;border-radius:8px;padding:8px 14px;
                    font-size:12px;color:#1e40af;margin-bottom:8px;">
                  📋 <strong>KRX 확정 최신일: {_latest_conf}</strong>
                  &nbsp;|&nbsp; 오늘({_dbg_today_str}) 기관·외국인 수급 <strong>{_st}</strong>
                  — 수급 확정치는 KRX 익일 09:00 이후 자동 반영됩니다.
                  &nbsp;|&nbsp; 갱신: 사이드바 ⚡ 버튼
                </div>""")
            else:
                st.html(f"""<div style="background:#f0fdf4;border-radius:8px;padding:8px 14px;
                    font-size:12px;color:#166534;margin-bottom:8px;">
                  ✅ <strong>KRX 확정 최신일: {_latest_conf}</strong>
                  &nbsp;|&nbsp; 최신 확정 데이터 반영 완료
                </div>""")

            # 종목별 잠정/확정 수급 테이블
            for t in top15_tickers:
                d = investor_map.get(t, [])
                name = result.loc[t, "종목명"] if t in result.index else t
                with st.expander(f"**{name}** ({t})", expanded=False):
                    st.html(_investor_html_table(d, t))

    elif st.session_state.get("analysis_run"):
        st.error(f"⚠️ {market_name} 데이터를 불러오지 못했습니다. 날짜를 확인해주세요 (공휴일·주말 불가).")
    else:
        st.html(f"""
        <div style="background:#fff;border-radius:20px;padding:40px;text-align:center;
                    box-shadow:0 2px 12px rgba(0,0,0,0.06);margin-top:12px;">
            <div style="font-size:48px;margin-bottom:12px;">{icon}</div>
            <div style="font-size:20px;font-weight:800;color:#13131a;margin-bottom:8px;">
                버튼을 눌러 {market_name} 분석을 시작하세요
            </div>
            <div style="font-size:14px;color:#9ca3af;line-height:1.8;">
                KOSPI와 KOSDAQ을 동시에 분석합니다.<br>
                기관·외국인 실데이터로 내일 급등 가능성을 계산합니다.
            </div>
        </div>""")


# ── 체급 탭 렌더 함수 ─────────────────────────────────────────────────────────
def render_tier_tab(grade_key: str):
    """KOSPI + KOSDAQ 합산 → 체급 필터링 후 카드 표시
    소형/동전주는 거래대금 TOP 15 밖 종목까지 확장 스캔"""
    gm = GRADE_META[grade_key]
    icon, name, desc, color, css, tip = gm

    st.html(f'<div class="section-header">{icon} {name} — KOSPI + KOSDAQ 합산</div>')
    st.html(f'<div class="section-sub">{tip} | 분류 기준: {desc}</div>')
    _run_btn(f"btn_tier_{grade_key}", f"🚀 {icon} {name} KOSPI+KOSDAQ 분석 시작")

    kp = st.session_state.get("kospi_ranked")
    kq = st.session_state.get("kosdaq_ranked")

    if kp is None and kq is None:
        if not st.session_state.get("analysis_run"):
            st.html(f"""
            <div style="background:#fff;border-radius:20px;padding:40px;text-align:center;
                        box-shadow:0 2px 12px rgba(0,0,0,0.06);margin-top:12px;">
                <div style="font-size:52px;margin-bottom:12px;">{icon}</div>
                <div style="font-size:18px;font-weight:800;color:#13131a;margin-bottom:8px;">
                    버튼을 눌러 분석을 시작하세요
                </div>
                <div style="font-size:14px;color:#9ca3af;">
                    KOSPI + KOSDAQ 전체 결과 중 {name} 종목만 자동으로 모아 보여줍니다.
                </div>
            </div>""")
        else:
            st.info("KOSPI · KOSDAQ 탭에서 분석이 완료되면 여기에 자동으로 표시됩니다.")
        return

    # ── TOP 15 scored 결과에서 해당 체급 필터 ─────────────────────────────
    parts = [df for df in [kp, kq] if df is not None]
    combined  = pd.concat(parts, ignore_index=True)
    filtered  = (combined[combined["_grade"] == grade_key]
                 .sort_values(["_exp_return", "_win_rate", "매수적합도(%)"], ascending=False)
                 .reset_index(drop=True))

    # ── 소형/동전주: TOP 15에 없으면 전체 price_df 에서 확장 스캔 ──────────
    if filtered.empty and grade_key == "small":
        extra_parts = []
        for mkt in ["kospi", "kosdaq"]:
            pdf = st.session_state.get(f"{mkt}_price_df")
            inv = st.session_state.get(f"{mkt}_investor_map", {})
            nws = st.session_state.get(f"{mkt}_news_map", {})
            if pdf is not None and not pdf.empty:
                with st.spinner(f"🪙 {mkt.upper()} 소형/동전주 확장 스캔 중…"):
                    sm = build_ranked_small(pdf, inv, nws)
                if not sm.empty:
                    extra_parts.append(sm)
        if extra_parts:
            filtered = (pd.concat(extra_parts, ignore_index=True)
                        .sort_values(["_exp_return", "_win_rate", "매수적합도(%)"], ascending=False)
                        .reset_index(drop=True))

    if filtered.empty:
        st.html(f"""
        <div style="background:#fff;border-radius:16px;padding:32px;text-align:center;
                    box-shadow:0 2px 10px rgba(0,0,0,0.06);margin-top:12px;">
            <div style="font-size:40px;margin-bottom:8px;">{icon}</div>
            <div style="font-size:16px;font-weight:700;color:#9ca3af;">
                현재 분석 결과에서 {name} 종목이 없습니다.
            </div>
        </div>""")
        return

    filtered = filtered.copy()
    filtered["순위"] = range(1, len(filtered) + 1)

    avg_wr = filtered["_win_rate"].mean()
    avg_er = filtered["_exp_return"].mean()
    top_er = filtered["_exp_return"].max()
    cnt    = len(filtered)

    st.html(f"""
    <div class="macro-card" style="margin-bottom:8px;">
        <div style="display:flex;gap:24px;flex-wrap:wrap;font-size:13px;align-items:center;">
            <div>
                <span style="font-size:22px;font-weight:900;color:{color};">{cnt}종목</span>
                <span style="font-size:12px;color:#9ca3af;margin-left:4px;">{name}</span>
            </div>
            <div>📊 <strong>평균 승률</strong>:
                <span style="color:#16a34a;font-weight:800;">{avg_wr:.1f}%</span></div>
            <div>📈 <strong>평균 기대수익</strong>:
                <span style="color:#ef4444;font-weight:800;">+{avg_er:.2f}%</span></div>
            <div>🚀 <strong>최고 기대수익</strong>:
                <span style="color:#7c3aed;font-weight:800;">+{top_er:.2f}%</span>
                ({filtered.iloc[0]["종목명"]})</div>
        </div>
    </div>""")

    render_ranked_cards(filtered)


# ── KOSPI TAB ────────────────────────────────────────────────────────────────
with tab_kp:
    render_market_tab("KOSPI", "kospi_result", "kospi_date", "btn_kp", "KOSPI")

# ── KOSDAQ TAB ───────────────────────────────────────────────────────────────
with tab_kq:
    render_market_tab("KOSDAQ", "kosdaq_result", "kosdaq_date", "btn_kq", "KOSDAQ")

# ── 체급별 탭 ─────────────────────────────────────────────────────────────────
with tab_bc:
    render_tier_tab("bluechip")

with tab_mc:
    render_tier_tab("midcap")

with tab_sm:
    render_tier_tab("small")

# ── 수급 분석표 ───────────────────────────────────────────────────────────────
with tab_supply:
    st.html('<div class="section-header">📊 수급 분석표</div>')
    _run_btn("btn_sup")

    sub_k, sub_q = st.tabs(["🏆 KOSPI", "🔷 KOSDAQ"])
    for sub_tab, rkey, mname in [(sub_k,"kospi_result","KOSPI"),(sub_q,"kosdaq_result","KOSDAQ")]:
        with sub_tab:
            result = st.session_state.get(rkey)
            if result is not None and not result.empty:
                top15 = result.sort_values(["거래대금(억)","거래량비율(%)"], ascending=False).head(15)
                display = top15[["종목명","섹터","현재가","등락률(%)","거래대금(억)","거래량비율(%)","RSI","눌림목신호"]].copy()
                display.columns = ["종목명","섹터","현재가(원)","등락률(%)\n🔴상승 🔵하락",
                                   "거래대금(억)\n[오늘 거래금액]","거래량비율(%)\n[평균 대비]",
                                   "RSI\n[30↓과매도]","매수타이밍\n[눌림목신호]"]

                def _cs(v):
                    if isinstance(v,(int,float)):
                        if v < 0: return "color:#1d6ce8;font-weight:bold"
                        if v > 0: return "color:#ef4444;font-weight:bold"
                    return ""

                st.dataframe(
                    display.style
                    .background_gradient(subset=["거래대금(억)\n[오늘 거래금액]"], cmap="Reds", vmin=0)
                    .background_gradient(subset=["거래량비율(%)\n[평균 대비]"], cmap="Oranges", vmin=0)
                    .map(_cs, subset=["등락률(%)\n🔴상승 🔵하락"])
                    .format({
                        "현재가(원)":"{:,}","등락률(%)\n🔴상승 🔵하락":"{:+.2f}%",
                        "거래대금(억)\n[오늘 거래금액]":"{:,.1f}억",
                        "거래량비율(%)\n[평균 대비]":"{:.1f}%",
                        "RSI\n[30↓과매도]":"{:.1f}",
                    }), width="stretch", height=520)

                _export_df = top15.reset_index()
                _export_df.rename(columns={"index": "종목코드"}, inplace=True)
                _csv_date  = st.session_state.get(f"{'kospi' if mname=='KOSPI' else 'kosdaq'}_date", datetime.now(KST).strftime("%Y-%m-%d"))
                _csv_bytes = _export_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button(
                    label="⬇️ CSV 다운로드",
                    data=_csv_bytes,
                    file_name=f"숨비애널리틱스_{mname}_{_csv_date}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.info(f"{mname} 분석 후 데이터가 표시됩니다.")

# ── 섹터 흐름 ─────────────────────────────────────────────────────────────────
with tab_sector:
    st.html('<div class="section-header">💰 어디에 돈이 몰리고 있나요?</div>')
    sub_k2, sub_q2 = st.tabs(["🏆 KOSPI 섹터", "🔷 KOSDAQ 섹터"])
    for sub_tab, rkey, mname in [(sub_k2,"kospi_result","KOSPI"),(sub_q2,"kosdaq_result","KOSDAQ")]:
        with sub_tab:
            result = st.session_state.get(rkey)
            if result is not None and not result.empty:
                sdf   = get_sector_flow(result)
                top3s = sdf.head(3)
                sc    = st.columns(3)
                for i, (_, row) in enumerate(top3s.iterrows()):
                    with sc[i]:
                        st.html(f"""
                        <div class="index-card">
                            <div class="index-name">{"🥇🥈🥉"[i]} {row['섹터']}</div>
                            <div class="index-value up">{row['섹터 거래대금(억)']:,.0f}억</div>
                            <div class="index-delta up">전체의 {row['비중(%)']:.1f}%</div>
                        </div>""")
                st.bar_chart(sdf.set_index("섹터")["섹터 거래대금(억)"], color="#ef4444")
                st.dataframe(sdf, width="stretch")
                if not top3s.empty:
                    ts = top3s.iloc[0]["섹터"]
                    st.html(f"""
                    <div class="macro-card">
                        <div style="font-size:13px;color:#374151;">
                        💡 <strong>{mname}</strong>에서 오늘 자금은
                        <strong style="color:#ef4444;">{ts}</strong> 섹터에 가장 많이 집중됐습니다.
                        해당 섹터 대장주에 추가 수급 유입 가능성을 주시하세요.
                        </div>
                    </div>""")
            else:
                st.info(f"{mname} 분석 후 데이터가 표시됩니다.")

# ── 미반영 뉴스 ───────────────────────────────────────────────────────────────
with tab_news:
    st.html('<div class="section-header">📰 주가에 아직 반영 안 된 뉴스</div>')
    st.html('<div class="section-sub">종목명이 포함된 기사만 수집 → 호재·악재·미반영 호재 3단 분류. 중립 기사는 표시하지 않습니다.</div>')
    sub_kn, sub_qn = st.tabs(["🏆 KOSPI", "🔷 KOSDAQ"])
    for sub_tab, rkey, mname in [(sub_kn,"kospi_result","KOSPI"),(sub_qn,"kosdaq_result","KOSDAQ")]:
        with sub_tab:
            result = st.session_state.get(rkey)
            if result is not None and not result.empty:
                top15n = result.sort_values(["거래대금(억)","거래량비율(%)"], ascending=False).head(15)
                nm     = get_news_batch(tuple(top15n.index.tolist()))
                for ticker in top15n.index:
                    name      = top15n.loc[ticker, "종목명"]
                    raw_hl    = nm.get(ticker, [])
                    # 1) 종목명 필터링
                    headlines = filter_news_by_name(raw_hl, name)
                    if not headlines:
                        headlines = raw_hl  # fallback: 전체

                    # 2) 분류
                    unref_hl, good_hl, bad_hl = [], [], []
                    for h in headlines:
                        cat, kws = classify_news_item(h)
                        kw_str = f" [{', '.join(kws)}]" if kws else ""
                        if   cat == "미반영 호재": unref_hl.append(f"🔥 {h}{kw_str}")
                        elif cat == "호재":        good_hl.append(f"🟢 {h}{kw_str}")
                        elif cat == "악재":        bad_hl.append(f"🔴 {h}{kw_str}")

                    has_unref = bool(unref_hl)
                    has_sig   = bool(unref_hl or good_hl or bad_hl)
                    if has_unref:
                        icon, badge = "🔥", f"  미반영 호재 {len(unref_hl)}건"
                    elif good_hl:
                        icon, badge = "🟢", f"  호재 {len(good_hl)}건"
                    elif bad_hl:
                        icon, badge = "🔴", f"  악재 {len(bad_hl)}건"
                    else:
                        icon, badge = "📌", ""

                    with st.expander(f"{icon} {name} ({ticker}){badge}", expanded=has_unref):
                        if not headlines:
                            st.write("뉴스를 불러오지 못했습니다.")
                        elif not has_sig:
                            st.caption("유의미 시그널(호재·악재·미반영 호재)이 없습니다.")
                        else:
                            for line in unref_hl: st.markdown(line)
                            for line in good_hl:  st.markdown(line)
                            for line in bad_hl:   st.markdown(line)
                            if has_unref:
                                st.success(f"✅ 미반영 호재 감지 — 주가 선반영 전 선취매 검토")
            else:
                st.info(f"{mname} 분석 후 데이터가 표시됩니다.")

# ── 물량 주의 종목 ─────────────────────────────────────────────────────────────
with tab_oh:
    st.html('<div class="section-header">⚠️ 물량 주의 종목 감지</div>')
    st.html("""
    <div class="section-sub">
    오버행(물량 주의) = CB·블록딜 등 시장에 나올 수 있는 대량 매도 물량.
    안전핀(🛡️) = 물량이 있지만 주가 하방 경직 상태.
    </div>""")
    st.html("""
    <div class="macro-card">
        <div style="font-size:13px;color:#374151;line-height:2.1;">
        📌 <strong>오버행(Overhang)</strong> = 수면 위 빙하처럼 시장에 나올 준비된 대량 매도 물량<br>
        📌 <strong>CB(전환사채)</strong> = 대출을 주식으로 바꿀 수 있는 채권. 주가 오르면 매도 가능 → 부담<br>
        📌 <strong>블록딜(PRS)</strong> = 대주주가 대량 주식을 파는 것. 시장에 물량 부담 발생<br>
        📌 <strong>안전핀</strong> = 물량이 있어도 주가가 더 안 빠짐 → 오히려 매수 기회!
        </div>
    </div>""")

    oh_rows = []
    for h in detect_overhang(list(OVERHANG_DB.keys())):
        t = h["종목코드"]
        s = KOSPI_STOCKS if t in KOSPI_STOCKS else KOSDAQ_STOCKS
        oh_rows.append({
            "종목명": s[t][0] if t in s else t, "코드": t,
            "물량 유형": h["type"],
            "상태": "🛡️ 안전핀(하방 경직)" if h["safe"] else "⚠️ 물량 주의",
            "AI 분석": h["comment"],
        })
    if oh_rows:
        st.dataframe(pd.DataFrame(oh_rows), width="stretch")

    for h in detect_overhang(list(OVERHANG_DB.keys())):
        t    = h["종목코드"]
        s    = KOSPI_STOCKS if t in KOSPI_STOCKS else KOSDAQ_STOCKS
        name = s[t][0] if t in s else t
        icon = "🛡️ 안전핀" if h["safe"] else "⚠️ 주의"
        with st.expander(f"{icon} — {name} ({t}) · {h['type']}", expanded=False):
            st.markdown(f"**유형:** `{h['type']}`")
            st.markdown(f"**분석:** {h['comment']}")
            if h["safe"]:
                st.success("✅ **안전핀 상태**: 물량 있지만 하방 경직 — 오히려 안전한 매수 타점일 수 있습니다.")
            else:
                st.warning("⚠️ **물량 주의**: 대량 매도 출회 시 단기 하락 가능. 손절선 설정 필수.")
