"""
숨비 애널리틱스 v3.0 (SOOMBI Analytics)
- 시장 분리 랭킹: KOSPI TOP 15 / KOSDAQ TOP 15
- 종목 체급 자동 분류: 👑대장주(시총1조+) / ⚖️중형주(2천억~1조) / 🪙소형/동전주(2천억미만·주가2천원미만)
- 내일 급등 확률: 기대수익률 + 승률 계산
- 4대 필살기: 기관/연기금 × 공매도상환 × 눌림목 × 미반영호재
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
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
    """
    if market_cap >= 10_000:
        return "bluechip"
    if market_cap < 2_000 or close_price < 2_000:
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
@st.cache_data(ttl=600)
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


@st.cache_data(ttl=600)
def get_investor_batch(tickers: tuple) -> dict:
    return {t: get_investor_data_naver(t) for t in tickers}


@st.cache_data(ttl=600)
def get_naver_news(ticker: str) -> list:
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
                if title: out.append(f"[{d_el.get_text(strip=True)}] {title}")
            if len(out) >= 5: break
        return out
    except Exception:
        return []


@st.cache_data(ttl=600)
def get_news_batch(tickers: tuple) -> dict:
    return {t: get_naver_news(t) for t in tickers}


# ── 뉴스 분류 키워드 ──────────────────────────────────────────────────────────
_GOOD_KW = [
    "수주","계약체결","계약","임상성공","기술수출","어닝서프라이즈","흑자전환","흑자",
    "신사업","투자유치","특허","수혜","정책수혜","매출증가","수출","배당증가",
    "자사주매입","자사주","깜짝실적","실적개선","신고가","급등","호실적","수주잔고",
]
_BAD_KW = [
    "적자","손실","소송","제재","횡령","배임","부도","파산","리콜","감소",
    "취소","지연","하락","전환사채","유상증자","오버행","조사착수","피소",
    "징계","과태료","하향","경고","불공정","압수수색","혐의","기소",
]

def classify_news_item(headline: str) -> tuple:
    """Returns ('호재'|'악재'|'중립', matched_keywords)"""
    g = [kw for kw in _GOOD_KW if kw in headline]
    b = [kw for kw in _BAD_KW  if kw in headline]
    if len(g) > len(b): return "호재", g[:3]
    if len(b) > len(g): return "악재", b[:3]
    if g: return "호재", g[:3]
    if b: return "악재", b[:3]
    return "중립", []


@st.cache_data(ttl=300)
def sniper_price(ticker: str, suffix: str, date_str: str) -> dict:
    """단일 종목 가격·기술분석 데이터"""
    target_dt = datetime.strptime(date_str, "%Y%m%d")
    raw = yf.download(
        ticker + suffix,
        start=(target_dt - timedelta(days=70)).strftime("%Y-%m-%d"),
        end=(target_dt + timedelta(days=2)).strftime("%Y-%m-%d"),
        auto_adjust=True, progress=False,
    )
    if raw.empty:
        return {}
    # 단일 종목은 컬럼이 MultiIndex 아닐 수 있음
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    if "Close" not in raw.columns:
        return {}
    close  = raw["Close"].dropna()
    volume = raw["Volume"].dropna()
    if len(close) < 11:
        return {}
    cur   = float(close.iloc[-1])
    prev  = float(close.iloc[-2])
    vol   = float(volume.iloc[-1])
    avg20 = float(volume.tail(20).mean())
    pb    = calc_pullback_score(close, volume)
    ma5   = float(close.rolling(5).mean().iloc[-1])
    ma10  = float(close.rolling(10).mean().iloc[-1])
    ma20_ = float(close.rolling(20).mean().iloc[-1])
    try:
        mcap = round((yf.Ticker(ticker + suffix).fast_info.get("market_cap") or 0) / 1e8, 0)
    except Exception:
        mcap = 0.0
    return {
        "현재가":      round(cur),
        "등락률":      round((cur - prev) / prev * 100, 2),
        "거래량비율":  round(vol / avg20 * 100, 1),
        "거래대금":    round(cur * vol / 1e8, 1),
        "눌림목점수":  pb["score"],
        "눌림목신호":  pb["signal"],
        "RSI":         pb["rsi"],
        "ma5":         round(ma5),
        "ma10":        round(ma10),
        "ma20":        round(ma20_),
        "시가총액":    mcap,
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
    stocks    = KOSPI_STOCKS if market == "KOSPI" else KOSDAQ_STOCKS
    suffix    = SUFFIX[market]
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

    # 시가총액 병렬 조회 (yfinance fast_info)
    def _one_cap(t_sfx: str) -> float:
        try:
            return round((yf.Ticker(t_sfx).fast_info.get("market_cap") or 0) / 1e8, 0)
        except Exception:
            return 0.0
    with ThreadPoolExecutor(max_workers=10) as ex:
        caps = list(ex.map(_one_cap, [t + suffix for t in df.index]))
    df["시가총액(억)"] = caps

    return df.dropna(subset=["현재가","거래대금(억)"]).query("`거래대금(억)` > 0"), actual_date


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
    """코드/이름/부분명 검색 → (code, market, name, sector) or None"""
    q = q.strip()
    if q in _CODE_MKT:
        code = q; mkt = _CODE_MKT[q]
        name, sector = _ALL_STKS[code]
        return code, mkt, name, sector
    if q in _NAME_CODE:
        code = _NAME_CODE[q]; mkt = _CODE_MKT[code]
        name, sector = _ALL_STKS[code]
        return code, mkt, name, sector
    for code, (name, sector) in _ALL_STKS.items():
        if q in name:
            return code, _CODE_MKT[code], name, sector
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
        if _sinv:
            st.html('<div style="font-size:14px;font-weight:800;color:#13131a;margin:8px 0 4px;">🏦 기관·외국인 수급 흐름 (최근 5거래일)</div>')
            _inv_df = pd.DataFrame(_sinv)
            _inv_df.columns = ["날짜", "기관 순매수", "외국인 순매수", "외국인 보유율(%)"]
            st.dataframe(_inv_df, use_container_width=True, hide_index=True)

        # ── 뉴스 분류 ────────────────────────────────────────────────────────
        if _snews:
            st.html('<div style="font-size:14px;font-weight:800;color:#13131a;margin:12px 0 4px;">📰 뉴스 자동 분류 — 호재 · 악재 · 중립</div>')
            _good_html = _bad_html = _neut_html = ""
            _good_cnt = _bad_cnt = 0
            for _h in _snews:
                _cat, _kws = classify_news_item(_h)
                _kw_tag = (f' <span style="font-size:10px;color:#6b7280;">[{", ".join(_kws)}]</span>'
                           if _kws else "")
                if _cat == "호재":
                    _good_html += f'<div class="nc-good">🟢 {_h}{_kw_tag}</div>'
                    _good_cnt  += 1
                elif _cat == "악재":
                    _bad_html  += f'<div class="nc-bad">🔴 {_h}{_kw_tag}</div>'
                    _bad_cnt   += 1
                else:
                    _neut_html += f'<div class="nc-neut">⚪ {_h}</div>'

            _sum_color = ("#16a34a" if _good_cnt > _bad_cnt
                          else "#dc2626" if _bad_cnt > _good_cnt else "#94a3b8")
            _sum_text  = (f"호재 {_good_cnt}건 우세 — 긍정 편향" if _good_cnt > _bad_cnt
                          else f"악재 {_bad_cnt}건 우세 — 부정 편향" if _bad_cnt > _good_cnt
                          else "호재·악재 균형")
            st.html(f"""
<div style="background:{_sum_color}18;border-radius:10px;padding:9px 14px;margin-bottom:8px;
            border:1px solid {_sum_color}40;font-size:13px;font-weight:700;color:{_sum_color};">
    📊 뉴스 종합 ({len(_snews)}건): {_sum_text}
</div>
{_good_html}{_bad_html}{_neut_html}""")

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
        _kp_df, _kp_date = get_price_data(date_str, "KOSPI")
        _kq_df, _kq_date = get_price_data(date_str, "KOSDAQ")

    if _kp_df is not None and not _kp_df.empty:
        st.session_state["kospi_result"] = _kp_df
        st.session_state["kospi_date"]   = _kp_date
    else:
        st.session_state["kospi_result"] = None

    if _kq_df is not None and not _kq_df.empty:
        st.session_state["kosdaq_result"] = _kq_df
        st.session_state["kosdaq_date"]   = _kq_date
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


def _run_btn(key: str):
    if st.button("🚀 KOSPI · KOSDAQ 동시 분석 시작", key=key, use_container_width=True):
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

    _run_btn(run_btn_key)
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
        st.session_state[f"{market_code.lower()}_ranked"] = ranked

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
        with st.expander("🔍 기관·외국인 실데이터 원본 확인", expanded=False):
            debug_rows = []
            for t in top15_tickers:
                d = investor_map.get(t, [])
                name = result.loc[t, "종목명"] if t in result.index else t
                if d:
                    debug_rows.append({
                        "종목": f"{name}({t})", "당일 기관": f"{d[0]['기관']:+,}",
                        "당일 외국인": f"{d[0]['외국인']:+,}",
                        "외국인 보유율": f"{d[0]['보유율']:.2f}%",
                        "D-1 기관": f"{d[1]['기관']:+,}" if len(d)>1 else "—",
                        "D-2 기관": f"{d[2]['기관']:+,}" if len(d)>2 else "—",
                    })
                else:
                    debug_rows.append({"종목": f"{name}({t})", "당일 기관": "수집 실패",
                                       "당일 외국인":"—","외국인 보유율":"—","D-1 기관":"—","D-2 기관":"—"})
            st.dataframe(pd.DataFrame(debug_rows), width="stretch")
            st.caption("※ 네이버금융 frgn.naver 직접 파싱 — 기관합계에 연기금 포함")

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
    """KOSPI + KOSDAQ 합산 → 체급 필터링 후 카드 표시"""
    gm = GRADE_META[grade_key]
    icon, name, desc, color, css, tip = gm

    st.html(f'<div class="section-header">{icon} {name} — KOSPI + KOSDAQ 합산</div>')
    st.html(f'<div class="section-sub">{tip} | 분류 기준: {desc}</div>')
    _run_btn(f"btn_tier_{grade_key}")

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

    parts = [df for df in [kp, kq] if df is not None]
    combined = pd.concat(parts, ignore_index=True)
    filtered = (combined[combined["_grade"] == grade_key]
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
    if "순위" in filtered.columns:
        filtered.drop(columns=["순위"], inplace=True)
    filtered.insert(0, "순위", range(1, len(filtered) + 1))

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
    sub_kn, sub_qn = st.tabs(["🏆 KOSPI", "🔷 KOSDAQ"])
    for sub_tab, rkey, mname in [(sub_kn,"kospi_result","KOSPI"),(sub_qn,"kosdaq_result","KOSDAQ")]:
        with sub_tab:
            result = st.session_state.get(rkey)
            if result is not None and not result.empty:
                top15n = result.sort_values(["거래대금(억)","거래량비율(%)"], ascending=False).head(15)
                nm     = get_news_batch(tuple(top15n.index.tolist()))
                for ticker in top15n.index:
                    name      = top15n.loc[ticker,"종목명"]
                    headlines = nm.get(ticker, [])
                    hits      = [kw for kw in NEWS_KEYWORDS if any(kw in h for h in headlines)]
                    has_hot   = bool(hits)
                    badge     = f"  🔥 호재 키워드: {', '.join(hits)}" if has_hot else ""
                    with st.expander(f"{'🔥' if has_hot else '📌'} {name} ({ticker}){badge}",
                                     expanded=has_hot):
                        if headlines:
                            for h in headlines: st.markdown(f"- {h}")
                            if hits:
                                st.success(f"✅ 호재 키워드 감지: **{', '.join(hits)}** — 현재 주가에 미반영 가능성 체크!")
                        else:
                            st.write("뉴스를 불러오지 못했습니다.")
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
