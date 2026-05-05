"""
숨비 애널리틱스 (SOOMBI Analytics)
- 주가/OHLCV: yfinance | 기관/외국인 실데이터: 네이버금융 직접 파싱
- 4대 필살기 필터: 기관/연기금 × 숏스퀴즈 × 눌림목 × 미반영 호재
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="숨비 애널리틱스 · SOOMBI Analytics",
    page_icon="🐳",
    layout="wide",
)

# ───────────────────────────────────────────────────────────────────────────────
# 글로벌 CSS — 토스증권 스타일
# ───────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ─── 기본 폰트 & 배경 ─── */
html, body, [class*="css"] {
    font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
}
.main { background: #f8f9fc; }

/* ─── 지수 카드 ─── */
.index-card {
    background: #ffffff;
    border-radius: 20px;
    padding: 22px 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    margin-bottom: 8px;
    border: 1px solid #f0f0f5;
}
.index-name  { font-size: 13px; font-weight: 600; color: #8c8c9e; letter-spacing: 0.5px; margin-bottom: 6px; }
.index-value { font-size: 28px; font-weight: 800; color: #13131a; line-height: 1.1; }
.index-delta { font-size: 14px; font-weight: 700; margin-top: 5px; }
.up   { color: #ef4444; }   /* 한국식: 상승=빨강 */
.down { color: #1d6ce8; }   /* 한국식: 하락=파랑 */
.flat { color: #9ca3af; }

/* ─── 섹션 헤더 ─── */
.section-header {
    font-size: 20px; font-weight: 800; color: #13131a;
    margin: 28px 0 12px 0; letter-spacing: -0.3px;
}
.section-sub {
    font-size: 13px; color: #8c8c9e; margin-top: -8px; margin-bottom: 16px;
}

/* ─── 종목 카드 ─── */
.stock-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 20px 22px;
    margin-bottom: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    border-left: 5px solid #e2e8f0;
    transition: box-shadow 0.2s;
}
.stock-card.tier1 { border-left-color: #ef4444; }
.stock-card.tier2 { border-left-color: #f97316; }
.stock-card.tier3 { border-left-color: #eab308; }
.stock-card.tier4 { border-left-color: #94a3b8; }

.stock-rank  { font-size: 13px; font-weight: 700; color: #8c8c9e; }
.stock-name  { font-size: 19px; font-weight: 800; color: #13131a; margin: 2px 0 4px 0; }
.stock-price { font-size: 22px; font-weight: 800; color: #13131a; }
.stock-sector{ font-size: 12px; color: #9ca3af; background: #f1f5f9;
               border-radius: 6px; padding: 2px 8px; display:inline-block; }

/* ─── 적합도 바지 ─── */
.fit-bar-wrap { background: #f1f5f9; border-radius: 99px; height: 8px; margin: 8px 0 4px; }
.fit-bar      { border-radius: 99px; height: 8px; transition: width 0.4s; }

/* ─── 점수 배지 ─── */
.badge {
    display: inline-block; border-radius: 8px; padding: 3px 10px;
    font-size: 12px; font-weight: 700; margin: 2px 3px 2px 0;
}
.badge-inst  { background: #fef2f2; color: #dc2626; }
.badge-short { background: #fff7ed; color: #ea580c; }
.badge-pb    { background: #f0fdf4; color: #16a34a; }
.badge-news  { background: #eff6ff; color: #2563eb; }
.badge-hot   { background: #ef4444; color: #fff; }
.badge-safe  { background: #dbeafe; color: #1d4ed8; }
.badge-explode { background: #7c3aed; color: #fff; }

/* ─── 신호등 배지 ─── */
.signal-buy  { background:#ef4444; color:#fff; border-radius:10px;
               padding:4px 14px; font-size:13px; font-weight:800; }
.signal-ready{ background:#f59e0b; color:#fff; border-radius:10px;
               padding:4px 14px; font-size:13px; font-weight:800; }
.signal-wait { background:#94a3b8; color:#fff; border-radius:10px;
               padding:4px 14px; font-size:13px; font-height:800; }
.signal-stop { background:#e2e8f0; color:#64748b; border-radius:10px;
               padding:4px 14px; font-size:13px; }

/* ─── 매크로 코멘트 카드 ─── */
.macro-card {
    background:#ffffff; border-radius:16px; padding:20px 24px;
    box-shadow:0 2px 10px rgba(0,0,0,0.06); margin-bottom:12px;
}
.macro-line { font-size:14px; color:#374151; line-height:1.8; }

/* ─── 타이틀 ─── */
.soombi-title {
    font-size: 32px; font-weight: 900; color: #13131a; letter-spacing: -1px;
}
.soombi-sub {
    font-size: 14px; color: #8c8c9e; margin-top: 2px;
}
.soombi-logo { font-size: 36px; }

/* ─── 사이드바 ─── */
section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #f0f0f5;
}

/* ─── 분석 시작 버튼 ─── */
.stButton > button {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
    color: white !important; font-weight: 800 !important;
    border-radius: 14px !important; border: none !important;
    padding: 14px 28px !important; font-size: 16px !important;
    width: 100%; box-shadow: 0 4px 15px rgba(239,68,68,0.4) !important;
}

/* ─── 섹터 바 차트 제목 ─── */
h3 { font-weight: 800 !important; color: #13131a !important; }

/* ─── 탭 스타일 ─── */
[data-testid="stTabs"] button {
    font-weight: 700; font-size: 14px;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #ef4444 !important; border-bottom-color: #ef4444 !important;
}

/* ─── 데이터프레임 헤더 ─── */
thead tr th {
    background: #f8fafc !important; font-weight: 700 !important;
    font-size: 13px !important; color: #374151 !important;
}
</style>
""", unsafe_allow_html=True)


# ───────────────────────────────────────────────────────────────────────────────
# 종목 / 섹터 DB
# ───────────────────────────────────────────────────────────────────────────────
KOSPI_STOCKS = {
    "005930": ("삼성전자",          "반도체/IT"),
    "000660": ("SK하이닉스",        "반도체/IT"),
    "035420": ("NAVER",             "인터넷/플랫폼"),
    "005380": ("현대차",            "자동차"),
    "051910": ("LG화학",            "화학/배터리"),
    "006400": ("삼성SDI",           "화학/배터리"),
    "068270": ("셀트리온",          "바이오/헬스케어"),
    "105560": ("KB금융",            "금융"),
    "028260": ("삼성물산",          "건설/산업재"),
    "012330": ("현대모비스",        "자동차"),
    "207940": ("삼성바이오로직스",  "바이오/헬스케어"),
    "000270": ("기아",              "자동차"),
    "017670": ("SK텔레콤",          "통신"),
    "030200": ("KT",                "통신"),
    "015760": ("한국전력",          "에너지/유틸리티"),
    "034730": ("SK",                "지주/복합"),
    "032830": ("삼성생명",          "금융"),
    "086790": ("하나금융지주",      "금융"),
    "009540": ("HD현대중공업",      "조선/기계"),
    "010950": ("S-Oil",             "에너지/유틸리티"),
    "055550": ("신한지주",          "금융"),
    "024110": ("기업은행",          "금융"),
    "066570": ("LG전자",            "가전/전자"),
    "003550": ("LG",                "지주/복합"),
    "011200": ("HMM",               "운송/물류"),
    "034220": ("LG디스플레이",      "반도체/IT"),
    "009830": ("한화솔루션",        "화학/배터리"),
    "000100": ("유한양행",          "바이오/헬스케어"),
    "035720": ("카카오",            "인터넷/플랫폼"),
    "003490": ("대한항공",          "운송/물류"),
    "097950": ("CJ제일제당",        "소비재/음식"),
    "004020": ("현대제철",          "철강/소재"),
    "010130": ("고려아연",          "철강/소재"),
    "028050": ("삼성엔지니어링",    "건설/산업재"),
    "267250": ("HD현대",            "지주/복합"),
    "009150": ("삼성전기",          "반도체/IT"),
    "090430": ("아모레퍼시픽",      "소비재/음식"),
    "004170": ("신세계",            "유통/소비"),
    "004000": ("롯데케미칼",        "화학/배터리"),
    "005490": ("POSCO홀딩스",       "철강/소재"),
    "000810": ("삼성화재",          "금융"),
    "078930": ("GS",                "지주/복합"),
    "036460": ("한국가스공사",      "에너지/유틸리티"),
    "000720": ("현대건설",          "건설/산업재"),
    "016360": ("삼성증권",          "금융"),
    "139480": ("이마트",            "유통/소비"),
    "006800": ("미래에셋증권",      "금융"),
    "042660": ("한화오션",          "조선/기계"),
    "352820": ("하이브",            "엔터/미디어"),
    "035900": ("JYP엔터테인먼트",   "엔터/미디어"),
    "041510": ("SM엔터테인먼트",    "엔터/미디어"),
    "326030": ("SK바이오팜",        "바이오/헬스케어"),
    "033780": ("KT&G",              "소비재/음식"),
    "003670": ("포스코퓨처엠",      "화학/배터리"),
    "064350": ("현대로템",          "조선/기계"),
    "229640": ("LS ELECTRIC",       "전력/전기"),
    "069960": ("현대백화점",        "유통/소비"),
    "011780": ("금호석유",          "화학/배터리"),
    "011070": ("LG이노텍",          "반도체/IT"),
    "010140": ("삼성중공업",        "조선/기계"),
    "071050": ("한국금융지주",      "금융"),
    "377300": ("카카오페이",        "인터넷/플랫폼"),
    "112610": ("씨에스윈드",        "신재생에너지"),
    "008770": ("호텔신라",          "유통/소비"),
}

KOSDAQ_STOCKS = {
    "247540": ("에코프로비엠",        "화학/배터리"),
    "086520": ("에코프로",            "화학/배터리"),
    "196170": ("알테오젠",            "바이오/헬스케어"),
    "263750": ("펄어비스",            "게임"),
    "293490": ("카카오게임즈",        "게임"),
    "068760": ("셀트리온제약",        "바이오/헬스케어"),
    "028300": ("HLB",                 "바이오/헬스케어"),
    "045020": ("코스맥스",            "소비재/음식"),
    "214150": ("클래시스",            "의료기기"),
    "064760": ("티씨케이",            "반도체/IT"),
    "357780": ("솔브레인",            "반도체/IT"),
    "030520": ("한글과컴퓨터",        "반도체/IT"),
    "053800": ("안랩",                "반도체/IT"),
    "145720": ("덴티움",              "의료기기"),
    "068600": ("대원제약",            "바이오/헬스케어"),
    "323410": ("카카오뱅크",          "금융"),
    "039030": ("이오테크닉스",        "반도체/IT"),
    "131970": ("테크윙",              "반도체/IT"),
    "240810": ("원익IPS",             "반도체/IT"),
    "058470": ("리노공업",            "반도체/IT"),
    "009420": ("한올바이오파마",      "바이오/헬스케어"),
    "078340": ("컴투스",              "게임"),
    "036830": ("솔브레인홀딩스",      "화학/배터리"),
    "048260": ("오스템임플란트",      "의료기기"),
    "122870": ("와이지엔터테인먼트",  "엔터/미디어"),
    "067160": ("아프리카TV",          "인터넷/플랫폼"),
    "108490": ("로보티즈",            "로봇/AI"),
}

OVERHANG_DB = {
    "042660": {"type": "블록딜(PRS)", "safe": True,
               "comment": "대형 블록딜이지만 전략적 투자자 유치 목적. 하방 경직성 확보 '안전핀' 패턴."},
    "003670": {"type": "CB 전환",     "safe": True,
               "comment": "전환사채 물량 상존. 포스코그룹 지원 시 하방 지지선 역할."},
    "086520": {"type": "CB/블록딜",   "safe": False,
               "comment": "에코프로그룹 CB 물량 상존. 급등 시 차익실현 출회 주의."},
    "247540": {"type": "CB 전환",     "safe": False,
               "comment": "에코프로비엠 전환사채 물량 상존. 수급 급변 시 우선 점검."},
    "028300": {"type": "유상증자",    "safe": False,
               "comment": "HLB 유상증자 후 물량 부담 잔존. 임상 이벤트로 상쇄 가능."},
    "196170": {"type": "BW 잔액",    "safe": True,
               "comment": "알테오젠 BW 잔액 존재. 기술수출 모멘텀으로 상쇄 기대."},
    "035720": {"type": "블록딜",      "safe": False,
               "comment": "카카오 주요 주주 블록딜 전례. 추가 블록딜 리스크 모니터링."},
}

NEWS_KEYWORDS = ["정부", "정책", "수주", "어닝서프라이즈", "어닝 서프라이즈",
                 "신사업", "생태계", "수혜", "수주잔고", "실적", "깜짝실적"]
SUFFIX = {"KOSPI": ".KS", "KOSDAQ": ".KQ"}
NAVER_HDR = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Referer": "https://finance.naver.com/",
}


# ───────────────────────────────────────────────────────────────────────────────
# UI 헬퍼 함수
# ───────────────────────────────────────────────────────────────────────────────
def index_card_html(name: str, value: str, delta_pct: float, delta_abs: float) -> str:
    """한국식 지수 카드 (상승=빨강, 하락=파랑)"""
    if delta_pct > 0:
        cls = "up"; arrow = "▲"; sign = "+"
    elif delta_pct < 0:
        cls = "down"; arrow = "▼"; sign = ""
    else:
        cls = "flat"; arrow = ""; sign = ""
    return f"""
    <div class="index-card">
        <div class="index-name">{name}</div>
        <div class="index-value {cls}">{value}</div>
        <div class="index-delta {cls}">{arrow} {sign}{delta_pct:.2f}% &nbsp;
            <span style="font-weight:400;font-size:12px;color:#9ca3af;">
                ({sign}{delta_abs:,.2f})
            </span>
        </div>
    </div>"""


def fit_signal_html(score: float) -> str:
    """매수 적합도 신호등 HTML"""
    if score >= 75:
        return f"<span class='signal-buy'>🔴 즉시 매수</span>"
    elif score >= 55:
        return f"<span class='signal-ready'>🟡 매수 준비</span>"
    elif score >= 35:
        return f"<span class='signal-wait'>⚪ 관망</span>"
    else:
        return f"<span class='signal-stop'>🔵 진입 불가</span>"


def fit_bar_html(score: float) -> str:
    """매수 적합도 프로그레스 바"""
    if score >= 75:   bar_color = "#ef4444"
    elif score >= 55: bar_color = "#f59e0b"
    elif score >= 35: bar_color = "#94a3b8"
    else:             bar_color = "#1d6ce8"
    return f"""
    <div class="fit-bar-wrap">
        <div class="fit-bar" style="width:{score}%;background:{bar_color};"></div>
    </div>
    <div style="font-size:13px;font-weight:800;color:{bar_color};">{score:.1f}점 / 100점</div>"""


def chg_color(v: float) -> str:
    """한국식 등락률 색상"""
    if v > 0:  return "#ef4444"
    elif v < 0: return "#1d6ce8"
    return "#9ca3af"


def tier_class(rank: int) -> str:
    if rank == 1:       return "tier1"
    elif rank <= 3:     return "tier2"
    elif rank <= 7:     return "tier3"
    return "tier4"


def stock_card_html(rank: int, r: pd.Series) -> str:
    """개별 종목 카드 HTML"""
    tc      = tier_class(rank)
    medals  = {1: "🥇", 2: "🥈", 3: "🥉"}
    medal   = medals.get(rank, f"#{rank}")
    price   = int(r["현재가"]) if not pd.isna(r["현재가"]) else 0
    chg     = float(r["등락률(%)"])
    cc      = chg_color(chg)
    chg_sym = "▲" if chg > 0 else "▼" if chg < 0 else ""
    sign    = "+" if chg > 0 else ""
    fit     = float(r["매수적합도(%)"])
    sig_html = fit_signal_html(fit)
    bar_html = fit_bar_html(fit)

    # 배지
    badges = ""
    if r.get("_squeeze", False):
        badges += "<span class='badge badge-explode'>💥 급등 대기 [공매도 상환]</span>"
    if r.get("_safepin", False):
        badges += "<span class='badge badge-safe'>🛡️ 안전핀 타점 [물량 주의→경직]</span>"

    inst_raw = r.get("_기관당일", 0)
    frgn_raw = r.get("_외국인당일", 0)
    inst_txt = f"{inst_raw:+,}" if inst_raw != 0 else "수집중"
    frgn_txt = f"{frgn_raw:+,}" if frgn_raw != 0 else "수집중"

    # 4대 점수 배지
    score_badges = (
        f"<span class='badge badge-inst'>🏦 기관/연기금 {r['기관/연기금']:.0f}점</span>"
        f"<span class='badge badge-short'>💥 공매도상환 {r['숏스퀴즈']:.0f}점</span>"
        f"<span class='badge badge-pb'>📈 최적매수타임 {r['눌림목']:.1f}점</span>"
        f"<span class='badge badge-news'>📰 미반영호재 {r['뉴스호재']:.0f}점</span>"
    )

    return f"""
    <div class="stock-card {tc}">
        <div style="display:flex; align-items:flex-start; justify-content:space-between; flex-wrap:wrap; gap:8px;">
            <div style="flex:1; min-width:200px;">
                <div class="stock-rank">{medal} {rank}위 &nbsp;<span class="stock-sector">{r['섹터']}</span></div>
                <div class="stock-name">{r['종목명']}</div>
                <div>
                    <span class="stock-price" style="color:{cc};">{price:,}원</span>
                    &nbsp;<span style="font-size:15px;font-weight:700;color:{cc};">{chg_sym} {sign}{chg:.2f}%</span>
                </div>
                <div style="margin-top:6px;">{badges}</div>
                <div style="margin-top:4px;">{score_badges}</div>
            </div>
            <div style="min-width:180px; text-align:right;">
                <div>{sig_html}</div>
                {bar_html}
                <div style="font-size:11px;color:#9ca3af;margin-top:6px;">
                    기관 {inst_txt} | 외국인 {frgn_txt}
                </div>
            </div>
        </div>
        <div style="margin-top:12px; padding-top:10px; border-top:1px solid #f1f5f9;
                    font-size:13px; color:#374151; line-height:1.6;">
            💬 <strong>AI 타점 분석:</strong> {r['타점분석']}
        </div>
    </div>"""


# ───────────────────────────────────────────────────────────────────────────────
# 데이터 함수 (로직 동일, 캐시 유지)
# ───────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def get_investor_data_naver(ticker: str) -> list:
    try:
        r = requests.get(
            "https://finance.naver.com/item/frgn.naver",
            headers=NAVER_HDR, params={"code": ticker}, timeout=8,
        )
        r.encoding = "euc-kr"
        soup   = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table")
        if len(tables) < 4:
            return []

        def _int(s: str) -> int:
            s = s.replace(",", "").replace("+", "")
            for w in ("상승", "하락", "보합"):
                s = s.replace(w, "")
            try:    return int(s)
            except: return 0

        def _float(s: str) -> float:
            try:    return float(s.replace("%", "").strip())
            except: return 0.0

        result = []
        for row in tables[3].find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cells) >= 7 and len(cells[0]) == 10 and cells[0][4] == ".":
                result.append({
                    "날짜":   cells[0],
                    "기관":   _int(cells[5]),
                    "외국인": _int(cells[6]),
                    "보유율": _float(cells[8]) if len(cells) > 8 else 0.0,
                })
                if len(result) >= 5:
                    break
        return result
    except Exception:
        return []


@st.cache_data(ttl=600)
def get_investor_batch(tickers: tuple) -> dict:
    return {t: get_investor_data_naver(t) for t in tickers}


@st.cache_data(ttl=600)
def get_naver_news(ticker: str) -> list:
    try:
        r = requests.get(
            f"https://finance.naver.com/item/news_news.naver?code={ticker}&page=1",
            headers=NAVER_HDR, timeout=6,
        )
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
            if len(out) >= 5:
                break
        return out
    except Exception:
        return []


@st.cache_data(ttl=600)
def get_news_batch(tickers: tuple) -> dict:
    return {t: get_naver_news(t) for t in tickers}


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
    if 0 <= ma5_gap <= 3:   score += 25
    elif -1.5 <= ma5_gap < 0: score += 20

    ma10_gap = (cur - ma10c) / ma10c * 100
    if 0 <= ma10_gap <= 5:  score += 20
    elif -2 <= ma10_gap < 0: score += 15

    if ma5c > ma10c > ma20c: score += 15
    elif ma5c > ma10c:        score += 8

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
    stocks = KOSPI_STOCKS if market == "KOSPI" else KOSDAQ_STOCKS
    suffix = SUFFIX[market]
    target_dt = datetime.strptime(date_str, "%Y%m%d")
    raw = yf.download(
        [t + suffix for t in stocks],
        start=(target_dt - timedelta(days=70)).strftime("%Y-%m-%d"),
        end=(target_dt + timedelta(days=2)).strftime("%Y-%m-%d"),
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
    df.insert(0, "종목명",  [stocks[t][0] if t in stocks else t for t in df.index])
    df.insert(1, "섹터",    [stocks[t][1] if t in stocks else "기타" for t in df.index])
    df["눌림목점수"] = pb_scores
    df["눌림목신호"] = pb_signals
    df["RSI"]        = rsi_vals
    return df.dropna(subset=["현재가", "거래대금(억)"]).query("`거래대금(억)` > 0"), actual_date


def score_ticker(ticker: str, row: pd.Series, investor_map: dict, news_map: dict) -> dict:
    data   = investor_map.get(ticker, [])
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

    # Filter 2: 숏스퀴즈 (0~20)
    short_score = 0
    if len(data) >= 2:
        rf = [d["외국인"] for d in data[:3]]
        ri = [d["기관"]   for d in data[:3]]
        rh = [d["보유율"] for d in data[:3]]
        if rf[0] > 0 and any(f < 0 for f in rf[1:3]):
            short_score += 15; squeeze_flag = True
            labels.append("💥외국인매수전환(공매도상환추정)")
        elif rf[0] < 0 and ri[0] > 0:
            short_score += 10; labels.append("기관방어→하방경직")
        elif len(rf) >= 3 and all(f > 0 for f in rf[:3]):
            short_score += 5; labels.append("외국인3일연속매수")
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
    news_hits  = []
    news_text  = " ".join(news_map.get(ticker, []))
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
        comment = "물량 주의 종목이지만 주가 하방 경직 확인 + 쌍끌이 — 안전핀 타점"
    elif safepin_flag:
        comment = "잠재 물량(오버행)이 있으나 하방 경직성 확보 — 안전핀 최적 타점"
    elif news_hits and "🔥쌍끌이" in labels:
        comment = f"정책·실적 호재({','.join(news_hits[:2])}) + 기관/외국인 쌍끌이 — 즉시 선취"
    elif news_hits:
        comment = f"현재가에 미반영된 호재({','.join(news_hits[:3])}) — 이벤트 드리븐 진입 검토"
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

    return {
        "기관/연기금": inst_score, "숏스퀴즈": short_score,
        "눌림목": pb_score, "뉴스호재": news_score,
        "매수적합도(%)": round(total, 1), "타점분석": comment,
        "폭발후보": squeeze_flag, "안전핀": safepin_flag,
        "수급신호": " | ".join(labels) if labels else "—",
        "_기관당일": inst_d0, "_외국인당일": foreign_d0, "_기관연속일": inst_streak,
    }


@st.cache_data(ttl=60)
def get_macro_indices() -> dict:
    syms = {"KOSPI": "^KS11", "KOSDAQ": "^KQ11", "나스닥": "^IXIC", "나스닥선물": "NQ=F"}
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


# ───────────────────────────────────────────────────────────────────────────────
# ■ UI 시작 — 숨비 애널리틱스 헤더
# ───────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; align-items:center; gap:14px; padding:8px 0 16px;">
    <div class="soombi-logo">🐳</div>
    <div>
        <div class="soombi-title">숨비 애널리틱스</div>
        <div class="soombi-sub">SOOMBI Analytics · 4대 필살기 AI 매수 적합도 엔진</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── 지수 전광판 ───────────────────────────────────────────────────────────────
macro = get_macro_indices()
index_keys = ["KOSPI", "KOSDAQ", "나스닥", "나스닥선물"]
idx_cols   = st.columns(4)
for col, key in zip(idx_cols, index_keys):
    d = macro.get(key)
    with col:
        if d:
            v = f"{d['현재']:,.2f}" if d["현재"] < 100_000 else f"{d['현재']:,.0f}"
            st.markdown(index_card_html(key, v, d["변동률"], d["변동"]), unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="index-card">
                <div class="index-name">{key}</div>
                <div class="index-value flat">N/A</div>
            </div>""", unsafe_allow_html=True)

# ── 장세 코멘트 카드 ──────────────────────────────────────────────────────────
kd = macro.get("KOSPI"); nd = macro.get("나스닥"); nfd = macro.get("나스닥선물")
lines = []
if kd:
    if kd["변동률"] > 0.5:    lines.append(f"🔴 <strong>국내 증시 강세</strong>: KOSPI {kd['변동률']:+.2f}% — 기관·외국인 순매수 우위. 매수 여건 유리합니다.")
    elif kd["변동률"] < -0.5: lines.append(f"🔵 <strong>국내 증시 약세</strong>: KOSPI {kd['변동률']:+.2f}% — 외국인 이탈 또는 프로그램 매도. 관망 후 눌림목 진입 검토.")
    else:                      lines.append(f"⚪ <strong>국내 증시 보합</strong>: KOSPI {kd['변동률']:+.2f}% — 방향성 탐색 중. 개별 종목 수급에 집중하세요.")
if nd:
    if nd["변동률"] > 0.5:    lines.append(f"🔴 <strong>글로벌 상승</strong>: 나스닥 {nd['변동률']:+.2f}% — 반도체·성장주 수급 유리합니다.")
    elif nd["변동률"] < -0.5: lines.append(f"🔵 <strong>글로벌 하락</strong>: 나스닥 {nd['변동률']:+.2f}% — IT·바이오 수급 압박 주의.")
    else:                      lines.append(f"⚪ <strong>글로벌 보합</strong>: 나스닥 방향성 불명확 — 국내 수급 주도장 예상.")
if nfd:
    sign = "상승" if nfd["변동률"] >= 0 else "하락"
    lines.append(f"📡 <strong>나스닥 선물</strong>: {nfd['변동률']:+.2f}% {sign} — 다음 장 개장 분위기 선반영 중.")

macro_body = "<br>".join(lines) if lines else "시장 데이터를 불러오는 중입니다."
st.markdown(f"""
<div class="macro-card">
    <div style="font-size:14px;font-weight:800;color:#13131a;margin-bottom:10px;">📊 지금 시장은?</div>
    <div class="macro-line">{macro_body}</div>
    <div style="font-size:11px;color:#c4c4cf;margin-top:10px;">
        ※ 한국 증시 기준: 🔴 상승 | 🔵 하락 &nbsp;·&nbsp; 빨간색=오름, 파란색=내림
    </div>
</div>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────────
# 사이드바
# ───────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown("""
<div style="font-size:20px;font-weight:900;color:#13131a;padding:8px 0 4px;">🐳 숨비 애널리틱스</div>
<div style="font-size:12px;color:#9ca3af;margin-bottom:16px;">SOOMBI Analytics</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("**📅 분석 기간 설정**")
target_date = st.sidebar.date_input("기준일 선택", datetime.now() - timedelta(days=1), label_visibility="collapsed")
date_str    = target_date.strftime("%Y%m%d")
market_type = st.sidebar.selectbox("📈 시장 선택", ["KOSPI", "KOSDAQ"])

st.sidebar.markdown("---")
st.sidebar.markdown("**⚙️ 설정**")
if st.sidebar.button("🔄 데이터 새로고침", width="stretch"):
    if st.session_state.get("analysis_run"):
        st.cache_data.clear(); st.rerun()
    else:
        st.sidebar.info("먼저 분석을 시작하세요.")

auto_refresh = st.sidebar.toggle("자동 새로고침", value=False)
refresh_interval = 60
if auto_refresh:
    refresh_interval = st.sidebar.selectbox(
        "주기", [30, 60, 120, 300],
        format_func=lambda x: f"{x}초" if x < 60 else f"{x//60}분", index=1)
if auto_refresh and st.session_state.get("analysis_run"):
    cnt = st_autorefresh(interval=refresh_interval * 1000, key="autorefresh")
    if cnt > 0: st.cache_data.clear()

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="font-size:12px;color:#9ca3af;line-height:1.8;">
<strong>🐳 숨비(Soombi)란?</strong><br>
제주 해녀가 숨을 참고 깊이 잠수해<br>
귀한 것을 건져 올리는 전통 기술.<br>
깊이 분석해 급등 종목을 포착합니다.
</div>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────────
# 공통 데이터 페치
# ───────────────────────────────────────────────────────────────────────────────
if st.session_state.get("analysis_run"):
    with st.spinner("📈 주가 데이터를 불러오는 중입니다…"):
        _price_df, _actual_date = get_price_data(date_str, market_type)
    if _price_df is None or _price_df.empty:
        st.error(f"⚠️ {date_str} {market_type} 데이터가 없습니다. 공휴일·주말·미개장일인지 확인해주세요.")
        st.session_state["result"] = None
    else:
        st.session_state["result"]      = _price_df
        st.session_state["actual_date"] = _actual_date

# ───────────────────────────────────────────────────────────────────────────────
# 탭
# ───────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 AI 매수 추천 TOP 15",
    "📊 수급 분석표",
    "💰 섹터 돈의 흐름",
    "📰 미반영 뉴스",
    "⚠️ 물량 주의 종목",
])


def _run_btn(key: str):
    if st.button("🚀 지금 분석 시작하기", key=key, width="stretch"):
        st.session_state["analysis_run"] = True
        st.session_state["market"]  = market_type
        st.session_state["date"]    = date_str
        st.cache_data.clear()


# ── TAB 1: AI 매수 추천 랭킹 ─────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-header">🏆 AI 매수 추천 TOP 15</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-sub">
    🏦 기관·연기금 매집(30점) + 💥 공매도 상환 급등 대기(20점) +
    📈 최적 매수 타이밍 눌림목(30점) + 📰 미반영 뉴스 호재(20점) = 100점 만점
    </div>""", unsafe_allow_html=True)

    _run_btn("btn1")

    result = st.session_state.get("result")
    if result is not None and not result.empty:
        actual_date = st.session_state.get("actual_date", "")
        if actual_date and actual_date != target_date.strftime("%Y-%m-%d"):
            st.info(f"📅 **{actual_date}** 기준 (요청일 데이터 없음 → 최근 거래일로 대체)")

        top15_base    = result.sort_values(["거래대금(억)", "거래량비율(%)"], ascending=False).head(15)
        top15_tickers = tuple(top15_base.index.tolist())

        with st.spinner("🏦 기관·외국인 순매매 실데이터 수집 중 (네이버금융)…"):
            investor_map = get_investor_batch(top15_tickers)
        with st.spinner("📰 뉴스 호재 키워드 분석 중…"):
            news_map = get_news_batch(top15_tickers)

        # 점수 계산
        scored_rows = []
        for ticker, row in top15_base.iterrows():
            s = score_ticker(ticker, row, investor_map, news_map)
            scored_rows.append({
                "종목명": row["종목명"], "섹터": row["섹터"],
                "현재가": row["현재가"], "등락률(%)": row["등락률(%)"],
                "RSI": row["RSI"], "눌림목신호": row["눌림목신호"],
                "거래대금(억)": row["거래대금(억)"],
                "기관/연기금": s["기관/연기금"], "숏스퀴즈": s["숏스퀴즈"],
                "눌림목": s["눌림목"], "뉴스호재": s["뉴스호재"],
                "매수적합도(%)": s["매수적합도(%)"], "타점분석": s["타점분석"],
                "수급신호": s["수급신호"],
                "_squeeze": s["폭발후보"], "_safepin": s["안전핀"],
                "_기관당일": s["_기관당일"], "_외국인당일": s["_외국인당일"],
                "_기관연속일": s["_기관연속일"],
            })

        ranked = (
            pd.DataFrame(scored_rows, index=top15_base.index)
            .sort_values("매수적합도(%)", ascending=False)
            .reset_index()
        )
        ranked.insert(0, "순위", range(1, len(ranked) + 1))

        # ── 종목 카드 렌더링 ──────────────────────────────────────────────────
        for _, r in ranked.iterrows():
            st.markdown(stock_card_html(int(r["순위"]), r), unsafe_allow_html=True)

        # ── 실데이터 원본 확인 ────────────────────────────────────────────────
        with st.expander("🔍 기관·외국인 실데이터 원본 확인", expanded=False):
            debug_rows = []
            for t in top15_tickers:
                d = investor_map.get(t, [])
                name = top15_base.loc[t, "종목명"] if t in top15_base.index else t
                if d:
                    debug_rows.append({
                        "종목": f"{name}({t})",
                        "당일 기관": f"{d[0]['기관']:+,}",
                        "당일 외국인": f"{d[0]['외국인']:+,}",
                        "외국인 보유율": f"{d[0]['보유율']:.2f}%",
                        "D-1 기관": f"{d[1]['기관']:+,}" if len(d) > 1 else "—",
                        "D-2 기관": f"{d[2]['기관']:+,}" if len(d) > 2 else "—",
                    })
                else:
                    debug_rows.append({"종목": f"{name}({t})", "당일 기관": "수집 실패",
                                       "당일 외국인": "—", "외국인 보유율": "—", "D-1 기관": "—", "D-2 기관": "—"})
            st.dataframe(pd.DataFrame(debug_rows), width="stretch")
            st.caption("※ 네이버금융 frgn.naver 직접 파싱 — 기관합계에 연기금 포함")

    else:
        # 미분석 상태 안내 카드
        st.markdown("""
        <div style="background:#fff;border-radius:20px;padding:40px;text-align:center;
                    box-shadow:0 2px 12px rgba(0,0,0,0.06);margin-top:12px;">
            <div style="font-size:48px;margin-bottom:12px;">🐳</div>
            <div style="font-size:20px;font-weight:800;color:#13131a;margin-bottom:8px;">
                분석을 시작해보세요
            </div>
            <div style="font-size:14px;color:#9ca3af;line-height:1.8;">
                위 버튼을 누르면 기관·외국인 실데이터를 수집하고<br>
                AI가 매수 적합도 1위~15위를 즉시 산출합니다.
            </div>
        </div>""", unsafe_allow_html=True)


# ── TAB 2: 수급 분석표 ───────────────────────────────────────────────────────
with tab2:
    st.markdown(f'<div class="section-header">📊 {market_type} 수급 분석표</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">거래대금 상위 15개 종목의 기술적 수급 현황</div>', unsafe_allow_html=True)
    _run_btn("btn2")

    result = st.session_state.get("result")
    if result is not None and not result.empty:
        top15 = result.sort_values(["거래대금(억)", "거래량비율(%)"], ascending=False).head(15)

        # 컬럼 한글 설명 추가
        display = top15[["종목명", "섹터", "현재가", "등락률(%)", "거래대금(억)", "거래량비율(%)", "RSI", "눌림목신호"]].copy()
        display.columns = ["종목명", "섹터", "현재가(원)", "등락률(%)\n↑빨강↓파랑",
                           "거래대금(억)\n[오늘 거래금액]", "거래량비율(%)\n[평균 대비]",
                           "RSI\n[30↓과매도→매수기회]", "매수타이밍\n[눌림목신호]"]

        def _chg_style(v):
            if isinstance(v, (int, float)):
                if v < 0: return "color:#1d6ce8;font-weight:bold"
                if v > 0: return "color:#ef4444;font-weight:bold"
            return ""

        styled2 = (
            display.style
            .background_gradient(subset=["거래대금(억)\n[오늘 거래금액]"],  cmap="Reds", vmin=0)
            .background_gradient(subset=["거래량비율(%)\n[평균 대비]"], cmap="Oranges", vmin=0)
            .map(_chg_style, subset=["등락률(%)\n↑빨강↓파랑"])
            .format({
                "현재가(원)":                   "{:,}",
                "등락률(%)\n↑빨강↓파랑":       "{:+.2f}%",
                "거래대금(억)\n[오늘 거래금액]": "{:,.1f}억",
                "거래량비율(%)\n[평균 대비]":    "{:.1f}%",
                "RSI\n[30↓과매도→매수기회]":    "{:.1f}",
            })
        )
        st.dataframe(styled2, width="stretch", height=520)
        st.markdown("""
        <div class="macro-card" style="margin-top:12px;">
            <div style="font-size:13px;color:#374151;line-height:2;">
            📌 <strong>거래대금</strong> — 오늘 이 종목에 몰린 돈의 총액 (클수록 주목도 높음)<br>
            📌 <strong>거래량비율</strong> — 평소 대비 오늘 거래량 (200% 이상이면 이상 수급)<br>
            📌 <strong>RSI</strong> — 0~30: 너무 내렸다(매수기회), 70~100: 너무 올랐다(과열 주의)
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.info("위 버튼을 눌러 분석을 시작하세요.")


# ── TAB 3: 섹터 흐름 ─────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-header">💰 어디에 돈이 몰리고 있나요?</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">오늘 거래대금 기준 섹터별 자금 흐름</div>', unsafe_allow_html=True)

    result = st.session_state.get("result")
    if result is not None and not result.empty:
        sector_df = get_sector_flow(result)
        top3_sec  = sector_df.head(3)

        sc = st.columns(3)
        medals_sec = ["🥇", "🥈", "🥉"]
        for i, (_, row) in enumerate(top3_sec.iterrows()):
            with sc[i]:
                st.markdown(f"""
                <div class="index-card">
                    <div class="index-name">{medals_sec[i]} {row['섹터']}</div>
                    <div class="index-value up">{row['섹터 거래대금(억)']:,.0f}억</div>
                    <div class="index-delta up">전체의 {row['비중(%)']:.1f}% 집중</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.bar_chart(sector_df.set_index("섹터")["섹터 거래대금(억)"], color="#ef4444")
        st.dataframe(sector_df, width="stretch")

        if not top3_sec.empty:
            top_sec = top3_sec.iloc[0]["섹터"]
            st.markdown(f"""
            <div class="macro-card">
                <div style="font-size:14px;color:#374151;">
                💡 오늘 자금은 <strong style="color:#ef4444;">{top_sec}</strong> 섹터에 가장 많이 집중됐습니다.
                해당 섹터 대장주에 추가 수급 유입 가능성을 주시하세요.
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("AI 매수 추천 탭에서 먼저 분석을 실행하세요.")


# ── TAB 4: 한글 뉴스 ─────────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-header">📰 주가에 아직 반영 안 된 뉴스</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">오늘 나온 뉴스 중 주가가 아직 따라가지 못한 호재를 탐색합니다</div>',
                unsafe_allow_html=True)

    result = st.session_state.get("result")
    if result is not None and not result.empty:
        top15_n = result.sort_values(["거래대금(억)", "거래량비율(%)"], ascending=False).head(15)
        nm = get_news_batch(tuple(top15_n.index.tolist()))

        for ticker in top15_n.index:
            name      = top15_n.loc[ticker, "종목명"]
            headlines = nm.get(ticker, [])
            hits      = [kw for kw in NEWS_KEYWORDS if any(kw in h for h in headlines)]
            has_hot   = bool(hits)
            badge     = f"  🔥 호재 키워드: {', '.join(hits)}" if has_hot else ""
            with st.expander(f"{'🔥' if has_hot else '📌'} {name} ({ticker}){badge}", expanded=has_hot):
                if headlines:
                    for h in headlines:
                        st.markdown(f"- {h}")
                    if hits:
                        st.success(f"✅ 호재 키워드 감지: **{', '.join(hits)}** — 현재 주가에 미반영 가능성 체크!")
                    st.caption("※ 네이버금융 실시간 뉴스 | 뉴스가 현재가에 반영되지 않았을 수 있습니다.")
                else:
                    st.write("뉴스를 불러오지 못했습니다.")
    else:
        st.info("AI 매수 추천 탭에서 먼저 분석을 실행하세요.")


# ── TAB 5: 오버행/블록딜 ─────────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-header">⚠️ 물량 주의 종목 감지</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-sub">
    오버행(물량 주의) = CB·블록딜 등 대량 물량이 시장에 나올 수 있는 종목.
    안전핀(🛡️) = 물량이 있지만 주가가 더 안 빠지는 하방 경직 상태.
    </div>""", unsafe_allow_html=True)

    result = st.session_state.get("result")
    if result is not None and not result.empty:
        top15_oh = result.sort_values(["거래대금(억)", "거래량비율(%)"], ascending=False).head(15)
        hits     = detect_overhang(top15_oh.index.tolist())

        st.markdown("#### 오늘 TOP 15 내 물량 주의 종목")
        if hits:
            for h in hits:
                t     = h["종목코드"]
                stk   = KOSPI_STOCKS if t in KOSPI_STOCKS else KOSDAQ_STOCKS
                name  = stk[t][0] if t in stk else t
                icon  = "🛡️ 안전핀" if h["safe"] else "⚠️ 주의"
                with st.expander(f"{icon} — {name} ({t}) · {h['type']}", expanded=True):
                    st.markdown(f"**유형:** `{h['type']}`")
                    st.markdown(f"**분석:** {h['comment']}")
                    if h["safe"]:
                        st.success("✅ **안전핀 상태**: 물량이 있지만 주가 하방 경직 — 오히려 안전한 타점일 수 있습니다.")
                    else:
                        st.warning("⚠️ **물량 주의**: 대량 매도 물량 출회 시 단기 하락 가능. 손절선 설정 필수.")
        else:
            st.success("✅ 오늘 TOP 15에 물량 주의 종목이 없습니다. 수급이 비교적 깨끗합니다.")

        st.markdown("<br>**전체 물량 주의 모니터링**", unsafe_allow_html=True)
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

        st.markdown("""
        <div class="macro-card">
            <div style="font-size:13px;color:#374151;line-height:2;">
            📌 <strong>오버행(Overhang)</strong> = 수면 위 빙하처럼, 시장에 나올 준비된 대량 매도 물량<br>
            📌 <strong>CB(전환사채)</strong> = 대출을 주식으로 바꿀 수 있는 채권. 주가 오르면 팔 수 있어 부담.<br>
            📌 <strong>블록딜(PRS)</strong> = 대주주가 대량으로 주식을 파는 것. 시장에 물량 부담 발생.<br>
            📌 <strong>안전핀</strong> = 물량이 있어도 주가가 더 안 빠짐 → 오히려 매수 기회!
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.info("AI 매수 추천 탭에서 먼저 분석을 실행하세요.")
