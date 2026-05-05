"""
42대 필살기 주식 분석 엔진 v2.0
- 주가/OHLCV: yfinance (듀얼 엔진)
- 기관/외국인 순매매: 네이버금융 frgn.naver 직접 파싱 (pykrx 대체)
- 공매도/숏스퀴즈: 외국인 매수전환 패턴 + 보유율 추세 분석
- 뉴스: 네이버금융 news_news.naver 한글 파싱
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

st.set_page_config(page_title="42대 필살기 분석기", layout="wide")

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
    "Accept-Charset": "euc-kr",
}


# ───────────────────────────────────────────────────────────────────────────────
# ■ 네이버 금융 — 기관/외국인 순매매 (듀얼 엔진 핵심)
# ───────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def get_investor_data_naver(ticker: str) -> list:
    """
    네이버금융 frgn.naver 에서 기관/외국인 순매매량 + 외국인 보유율 최근 5일 반환.
    반환 형식: [{"날짜": "2026.05.04", "기관": 4335045, "외국인": 5214979, "보유율": 49.33}, ...]
    """
    try:
        r = requests.get(
            "https://finance.naver.com/item/frgn.naver",
            headers=NAVER_HDR, params={"code": ticker}, timeout=8,
        )
        r.encoding = "euc-kr"
        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table")
        if len(tables) < 4:
            return []

        target = tables[3]
        rows = target.find_all("tr")
        result = []

        def _parse_int(s: str) -> int:
            """'+4,335,045', '상승12,000', '-840,944' → int"""
            s = s.replace(",", "").replace("+", "")
            for w in ("상승", "하락", "보합"):
                s = s.replace(w, "")
            try:
                return int(s)
            except ValueError:
                return 0

        def _parse_float(s: str) -> float:
            try:
                return float(s.replace("%", "").strip())
            except ValueError:
                return 0.0

        for row in rows:
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            # 날짜 행: cells[0] = "2026.05.04", len >= 7
            if len(cells) >= 7 and len(cells[0]) == 10 and cells[0][4] == ".":
                result.append({
                    "날짜":    cells[0],
                    "기관":    _parse_int(cells[5]),
                    "외국인":  _parse_int(cells[6]),
                    "보유율":  _parse_float(cells[8]) if len(cells) > 8 else 0.0,
                })
                if len(result) >= 5:
                    break

        return result

    except Exception:
        return []


@st.cache_data(ttl=600)
def get_investor_batch(tickers: tuple) -> dict:
    """여러 티커의 기관/외국인 데이터를 한 번에 수집 (캐시 공유)."""
    return {t: get_investor_data_naver(t) for t in tickers}


# ───────────────────────────────────────────────────────────────────────────────
# ■ 네이버 금융 — 한글 뉴스
# ───────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def get_naver_news(ticker: str) -> list:
    try:
        url  = f"https://finance.naver.com/item/news_news.naver?code={ticker}&page=1"
        r    = requests.get(url, headers=NAVER_HDR, timeout=6)
        r.encoding = "euc-kr"
        soup = BeautifulSoup(r.text, "html.parser")
        out  = []
        for row in soup.select("table.type5 tr"):
            title_el = row.select_one("td.title a")
            date_el  = row.select_one("td.date")
            if title_el and date_el:
                title = title_el.get_text(strip=True)
                date  = date_el.get_text(strip=True)
                if title:
                    out.append(f"[{date}] {title}")
            if len(out) >= 5:
                break
        return out
    except Exception:
        return []


@st.cache_data(ttl=600)
def get_news_batch(tickers: tuple) -> dict:
    return {t: get_naver_news(t) for t in tickers}


# ───────────────────────────────────────────────────────────────────────────────
# ■ yfinance — OHLCV + 눌림목 분석 (기존 유지)
# ───────────────────────────────────────────────────────────────────────────────
def calc_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff().dropna()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta).clip(lower=0).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    rsi   = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not rsi.empty else 50.0


def calc_pullback_score(close_s: pd.Series, vol_s: pd.Series) -> dict:
    if len(close_s) < 22:
        return {"score": 0, "signal": "데이터 부족", "rsi": 50,
                "ma5": None, "ma10": None, "ma20": None}

    ma5  = close_s.rolling(5).mean()
    ma10 = close_s.rolling(10).mean()
    ma20 = close_s.rolling(20).mean()
    cur, prev = float(close_s.iloc[-1]), float(close_s.iloc[-2])
    ma5c  = float(ma5.iloc[-1]);  ma5p = float(ma5.iloc[-2])
    ma10c = float(ma10.iloc[-1])
    ma20c = float(ma20.iloc[-1])
    rsi   = calc_rsi(close_s)
    score = 0

    # 5일선 터치 (최적 눌림목)
    ma5_gap = (cur - ma5c) / ma5c * 100
    if 0 <= ma5_gap <= 3:
        score += 25
    elif -1.5 <= ma5_gap < 0:
        score += 20

    # 10일선 터치 (추세 생명선)
    ma10_gap = (cur - ma10c) / ma10c * 100
    if 0 <= ma10_gap <= 5:
        score += 20
    elif -2 <= ma10_gap < 0:
        score += 15

    # 정배열
    if ma5c > ma10c > ma20c:
        score += 15
    elif ma5c > ma10c:
        score += 8

    # 눌림 후 반등 양봉
    price_chg = (cur - prev) / prev * 100
    if price_chg > 0 and prev < ma5p:
        score += 20
    elif price_chg > 0:
        score += 10

    # RSI 최적 구간
    if 30 <= rsi <= 50:
        score += 20
    elif 50 < rsi <= 65:
        score += 10
    elif rsi < 30:
        score += 5

    score = min(score, 100)
    if score >= 75:   sig = "🔴 즉시 매수 (HIGH)"
    elif score >= 50: sig = "🟡 매수 준비 (MID)"
    elif score >= 30: sig = "⚪ 관망 (LOW)"
    else:             sig = "❌ 진입 불가"

    return {"score": score, "signal": sig, "rsi": round(rsi, 1),
            "ma5": round(ma5c, 0), "ma10": round(ma10c, 0), "ma20": round(ma20c, 0)}


@st.cache_data(ttl=300)
def get_price_data(date_str: str, market: str) -> tuple:
    stocks = KOSPI_STOCKS if market == "KOSPI" else KOSDAQ_STOCKS
    suffix = SUFFIX[market]
    yf_tickers = [t + suffix for t in stocks]

    target_dt = datetime.strptime(date_str, "%Y%m%d")
    raw = yf.download(
        yf_tickers,
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
            pb_scores.append(pb["score"])
            pb_signals.append(pb["signal"])
            rsi_vals.append(pb["rsi"])
        except Exception:
            pb_scores.append(0)
            pb_signals.append("N/A")
            rsi_vals.append(50)

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
    df = df.dropna(subset=["현재가", "거래대금(억)"]).query("`거래대금(억)` > 0")
    return df, actual_date


# ───────────────────────────────────────────────────────────────────────────────
# ■ 42대 필살기 마스터 스코어링 엔진 (4대 필터 완전 연동)
# ───────────────────────────────────────────────────────────────────────────────
def score_ticker(ticker: str, row: pd.Series,
                 investor_map: dict, news_map: dict) -> dict:
    """
    4대 필터 → 매수 적합도(0~100%) + 타점 분석 한줄평

    investor_map: {ticker: [{"날짜","기관","외국인","보유율"}, ...]}  ← 네이버 실데이터
    news_map:     {ticker: ["[날짜] 뉴스제목", ...]}
    """
    data    = investor_map.get(ticker, [])   # 최근 5일 기관/외국인 데이터
    labels  = []
    squeeze_flag = False
    safepin_flag = False

    # ── Filter 1: 기관/연기금 안전핀 (0~30점) ────────────────────────────────
    # 네이버 frgn.naver 실데이터: 기관합계(연기금 포함) + 외국인 순매매량
    inst_score = 0
    inst_d0 = foreign_d0 = 0
    inst_streak = 0

    if data:
        d0        = data[0]
        inst_d0   = d0["기관"]
        foreign_d0 = d0["외국인"]

        if inst_d0 > 0:
            inst_score += 8
            labels.append("기관매집")
        if foreign_d0 > 0:
            inst_score += 7
            labels.append("외국인매집")
        if inst_d0 > 0 and foreign_d0 > 0:
            inst_score += 5           # 쌍끌이 보너스
            labels.append("🔥쌍끌이")

        # 3일 연속 기관 순매수 = 연기금 포함 기관합계 지속 매집
        inst_streak = sum(1 for d in data[:3] if d["기관"] > 0)
        if inst_streak >= 3:
            inst_score += 10
            labels.append("💎기관3일연속(연기금포함)")
        elif inst_streak == 2:
            inst_score += 5
            labels.append("기관2일연속")

    inst_score = min(inst_score, 30)

    # ── Filter 2: 공매도 숏스퀴즈 & 신용 바닥 (0~20점) ─────────────────────
    # 네이버 실데이터 기반: 외국인 매수전환 패턴 + 보유율 추세
    short_score   = 0
    squeeze_label = ""

    if len(data) >= 2:
        recent_inst    = [d["기관"]    for d in data[:3]]
        recent_foreign = [d["외국인"]  for d in data[:3]]
        recent_hold    = [d["보유율"]  for d in data[:3]]

        # 패턴 A: 외국인 매도 → 매수 전환 (숏커버링 신호)
        if recent_foreign[0] > 0 and any(f < 0 for f in recent_foreign[1:3]):
            short_score  += 15
            squeeze_flag  = True
            squeeze_label = "💥외국인매수전환(숏커버링추정)"
            labels.append(squeeze_label)

        # 패턴 B: 외국인 매도 지속 but 기관 방어 → 하방 경직
        elif recent_foreign[0] < 0 and recent_inst[0] > 0:
            short_score += 10
            labels.append("기관방어vs외국인매도(하방경직)")

        # 패턴 C: 외국인 3일 연속 매수 → 안정 수급
        elif len(recent_foreign) >= 3 and all(f > 0 for f in recent_foreign[:3]):
            short_score += 5
            labels.append("외국인3일연속매수")

        # 보유율 상승 추세 (+5 보너스)
        if len(recent_hold) >= 2 and recent_hold[0] > recent_hold[1]:
            short_score = min(short_score + 5, 20)
            if "💥" not in " ".join(labels):
                labels.append("외국인보유율↑")

    short_score = min(short_score, 20)

    # ── Filter 3: 눌림목 & 오버행 안전핀 (0~30점) ───────────────────────────
    pb_raw   = float(row.get("눌림목점수", 0))
    pb_score = round(pb_raw * 0.30, 1)

    if ticker in OVERHANG_DB:
        oh = OVERHANG_DB[ticker]
        if oh["safe"] and pb_score >= 9:
            pb_score = min(pb_score + 5, 30)
            safepin_flag = True
            labels.append("🛡️안전핀타점")

    pb_score = min(pb_score, 30)

    # ── Filter 4: 미반영 호재 & 정책 수혜 키워드 (0~20점) ───────────────────
    news_score = 0
    news_hits  = []
    news_text  = " ".join(news_map.get(ticker, []))
    for kw in NEWS_KEYWORDS:
        if kw in news_text and kw not in news_hits:
            news_hits.append(kw)
    news_score = min(len(news_hits) * 4, 20)
    if news_hits:
        labels.append(f"📰호재({','.join(news_hits[:3])})")

    # ── 최종 매수 적합도 ──────────────────────────────────────────────────────
    total = min(inst_score + short_score + pb_score + news_score, 100)

    # ── 타점 분석 한줄평 ─────────────────────────────────────────────────────
    pb_sig = row.get("눌림목신호", "")
    rsi_v  = float(row.get("RSI", 50))
    chg    = float(row.get("등락률(%)", 0))
    vol_r  = float(row.get("거래량비율(%)", 100))

    if "💎기관3일연속(연기금포함)" in labels and "🔥쌍끌이" in labels:
        comment = "기관(연기금 포함)+외국인 쌍끌이 3일 집중 매집 — 즉시 진입 유효, 추세 가속 구간"
    elif "💎기관3일연속(연기금포함)" in labels:
        comment = "기관(연기금 포함) 3일 연속 순매수 — 공적 자금 하방 지지, 중장기 매집 강력"
    elif squeeze_flag and "🔴 즉시 매수" in pb_sig:
        comment = f"외국인 매수 전환(숏커버링 추정) + {pb_sig} — 반등 폭발 타이밍"
    elif squeeze_flag:
        comment = "외국인 매도→매수 전환 포착 — 숏커버링 유입 시 급등 대기"
    elif safepin_flag and "🔥쌍끌이" in labels:
        comment = "오버행 안전핀 확보 + 기관/외국인 쌍끌이 — 하방 경직 후 재상승 타점"
    elif safepin_flag:
        comment = "오버행 있으나 하방 경직성 확보 — PRS/CB 부담 소화 후 안전핀 타점"
    elif news_hits and "🔥쌍끌이" in labels:
        comment = f"정책·실적 호재({','.join(news_hits[:2])}) + 기관/외국인 쌍끌이 — 즉시 모멘텀 선취"
    elif news_hits:
        comment = f"미반영 호재({','.join(news_hits[:3])}) — 이벤트 드리븐 진입 검토"
    elif "🔴 즉시 매수" in pb_sig and "🔥쌍끌이" in labels:
        comment = f"5/10일선 눌림목 반등 + 쌍끌이 — RSI {rsi_v:.0f} 저점 탈출 최적 타점"
    elif "🔴 즉시 매수" in pb_sig:
        comment = f"5/10일선 지지 확인, RSI {rsi_v:.0f} 저점 — 거래량 증가 시 즉시 진입"
    elif vol_r > 200:
        comment = f"거래량 {vol_r:.0f}% 급증 이상수급 — 세력 개입 의심, 추격 진입 유의"
    elif chg > 0 and "기관매집" in labels:
        comment = f"기관 순매수 + 상승({chg:+.1f}%) — 기관 주도 상승 초기 단계"
    else:
        comment = f"수급강도 우위, 거래대금 {float(row.get('거래대금(억)', 0)):,.0f}억 — 분할 진입 검토"

    return {
        "기관/연기금":     inst_score,
        "숏스퀴즈":        short_score,
        "눌림목":          pb_score,
        "뉴스호재":        news_score,
        "매수적합도(%)":   round(total, 1),
        "타점분석":        comment,
        "폭발후보":        squeeze_flag,
        "안전핀":          safepin_flag,
        "수급신호":        " | ".join(labels) if labels else "—",
        # 수급 원본 (디버그용)
        "_기관당일":       inst_d0,
        "_외국인당일":     foreign_d0,
        "_기관연속일":     inst_streak,
    }


# ───────────────────────────────────────────────────────────────────────────────
# 섹터 흐름
# ───────────────────────────────────────────────────────────────────────────────
def get_sector_flow(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    s = df.groupby("섹터")["거래대금(억)"].sum().sort_values(ascending=False).reset_index()
    s.rename(columns={"거래대금(억)": "섹터 거래대금(억)"}, inplace=True)
    s["비중(%)"] = (s["섹터 거래대금(억)"] / s["섹터 거래대금(억)"].sum() * 100).round(1)
    return s


def detect_overhang(tickers: list) -> list:
    return [{"종목코드": t, **OVERHANG_DB[t]} for t in tickers if t in OVERHANG_DB]


# ───────────────────────────────────────────────────────────────────────────────
# 매크로 지수
# ───────────────────────────────────────────────────────────────────────────────
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


# ───────────────────────────────────────────────────────────────────────────────
# UI — 헤더
# ───────────────────────────────────────────────────────────────────────────────
st.title("🚀 42대 필살기 주식 분석 엔진 v2.0")
st.caption("듀얼 엔진: yfinance(OHLCV) × 네이버금융(기관/외국인 실데이터) × 4대 필살기 필터")
st.markdown("---")

macro = get_macro_indices()
mc = st.columns(4)
for col, key in zip(mc, ["KOSPI", "KOSDAQ", "나스닥", "나스닥선물"]):
    d = macro.get(key)
    with col:
        if d:
            val = f"{d['현재']:,.2f}" if d['현재'] < 100_000 else f"{d['현재']:,.0f}"
            st.metric(key, val, f"{d['변동률']:+.2f}%")
        else:
            st.metric(key, "N/A")

with st.expander("📊 장세 3줄 매크로 코멘트", expanded=True):
    kd  = macro.get("KOSPI");  nd = macro.get("나스닥"); nfd = macro.get("나스닥선물")
    if kd:
        if kd["변동률"] > 0.5:   st.markdown(f"🟢 **국내**: KOSPI {kd['변동률']:+.2f}% 강세 — 외국인/기관 순매수 우위.")
        elif kd["변동률"] < -0.5: st.markdown(f"🔴 **국내**: KOSPI {kd['변동률']:+.2f}% 약세 — 프로그램 매도 또는 외국인 이탈 점검.")
        else:                      st.markdown(f"⚪ **국내**: KOSPI {kd['변동률']:+.2f}% 보합 — 관망세, 수급 이벤트 주시.")
    if nd:
        if nd["변동률"] > 0.5:    st.markdown(f"🟢 **글로벌**: 나스닥 {nd['변동률']:+.2f}% 상승 — 반도체·성장주 수급 유리.")
        elif nd["변동률"] < -0.5: st.markdown(f"🔴 **글로벌**: 나스닥 {nd['변동률']:+.2f}% 하락 — IT·바이오 수급 압박.")
        else:                      st.markdown(f"⚪ **글로벌**: 나스닥 보합 — 방향성 불명확.")
    if nfd:
        sign = "상승" if nfd and nfd["변동률"] >= 0 else "하락"
        st.markdown(f"📡 **나스닥선물**: {nfd['변동률']:+.2f}% {sign} — 다음 장 개장 분위기 선반영.")

st.markdown("---")

# ───────────────────────────────────────────────────────────────────────────────
# 사이드바
# ───────────────────────────────────────────────────────────────────────────────
st.sidebar.header("🔍 분석 필터 설정")
target_date = st.sidebar.date_input("분석 기준일", datetime.now() - timedelta(days=1))
date_str    = target_date.strftime("%Y%m%d")
market_type = st.sidebar.selectbox("시장 선택", ["KOSPI", "KOSDAQ"])

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 새로고침")
if st.sidebar.button("🔄 데이터 새로고침"):
    if st.session_state.get("analysis_run"):
        st.cache_data.clear(); st.rerun()
    else:
        st.sidebar.info("먼저 분석을 시작해 주세요.")

auto_refresh = st.sidebar.toggle("자동 새로고침", value=False)
refresh_interval = 60
if auto_refresh:
    refresh_interval = st.sidebar.selectbox(
        "주기", [30, 60, 120, 300],
        format_func=lambda x: f"{x}초" if x < 60 else f"{x//60}분", index=1)
if auto_refresh and st.session_state.get("analysis_run"):
    cnt = st_autorefresh(interval=refresh_interval * 1000, key="autorefresh")
    if cnt > 0:
        st.cache_data.clear()

# ───────────────────────────────────────────────────────────────────────────────
# 공통 데이터 페치 (탭 이전 — 전 탭 공유)
# ───────────────────────────────────────────────────────────────────────────────
if st.session_state.get("analysis_run"):
    with st.spinner("📈 yfinance OHLCV 수집 중 (주가/차트/눌림목)…"):
        _price_df, _actual_date = get_price_data(date_str, market_type)

    if _price_df is None or _price_df.empty:
        st.error(f"⚠️ {date_str} {market_type} 데이터 없음 — 공휴일·주말·미개장일입니다. 날짜를 변경하세요.")
        st.session_state["result"] = None
    else:
        st.session_state["result"]      = _price_df
        st.session_state["actual_date"] = _actual_date

# ───────────────────────────────────────────────────────────────────────────────
# 탭
# ───────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 42대 필살기 랭킹 TOP 15",
    "📊 수급 분석표",
    "💰 섹터 돈의 흐름",
    "📰 미반영 뉴스 (한글)",
    "⚠️ 오버행/블록딜 감지",
])


def _run_btn(key: str):
    if st.button("🚀 42대 필살기 엔진 풀가동 분석 시작", key=key):
        st.session_state["analysis_run"] = True
        st.session_state["market"]  = market_type
        st.session_state["date"]    = date_str
        st.cache_data.clear()


# ── TAB 1: 통합 랭킹 ─────────────────────────────────────────────────────────
with tab1:
    st.subheader("🏆 42대 필살기 통합 랭킹 TOP 15")
    st.caption(
        "**배점**: 🏦 기관/연기금 실데이터(30점) + 💥 숏스퀴즈 패턴(20점) "
        "+ 📈 눌림목타점(30점) + 📰 미반영호재(20점) = **매수 적합도 100%**"
    )
    _run_btn("btn1")

    result = st.session_state.get("result")
    if result is not None and not result.empty:
        actual_date = st.session_state.get("actual_date", "")
        if actual_date and actual_date != target_date.strftime("%Y-%m-%d"):
            st.info(f"📅 최근 거래일 **{actual_date}** 기준으로 분석합니다.")

        # 초기 정렬로 TOP 15 추출 (거래대금 기준)
        top15_base = result.sort_values(
            by=["거래대금(억)", "거래량비율(%)"], ascending=False
        ).head(15)

        # 보조 데이터 수집 (네이버 실데이터)
        top15_tickers = tuple(top15_base.index.tolist())

        with st.spinner("🏦 네이버금융 기관/외국인 순매매 실데이터 수집 중…"):
            investor_map = get_investor_batch(top15_tickers)
        with st.spinner("📰 네이버금융 한글 뉴스 수집 중…"):
            news_map = get_news_batch(top15_tickers)

        # ── 수급 원본 디버그 정보 (확장) ─────────────────────────────────────
        with st.expander("🔍 기관/외국인 실데이터 수집 결과 확인 (원본)", expanded=False):
            debug_rows = []
            for t in top15_tickers:
                d = investor_map.get(t, [])
                name = top15_base.loc[t, "종목명"] if t in top15_base.index else t
                if d:
                    debug_rows.append({
                        "종목": f"{name}({t})",
                        "당일 기관": f"{d[0]['기관']:+,}" if d else "—",
                        "당일 외국인": f"{d[0]['외국인']:+,}" if d else "—",
                        "외국인 보유율": f"{d[0]['보유율']:.2f}%" if d else "—",
                        "D-1 기관": f"{d[1]['기관']:+,}" if len(d) > 1 else "—",
                        "D-2 기관": f"{d[2]['기관']:+,}" if len(d) > 2 else "—",
                    })
                else:
                    debug_rows.append({"종목": f"{name}({t})", "당일 기관": "데이터 없음",
                                       "당일 외국인": "—", "외국인 보유율": "—",
                                       "D-1 기관": "—", "D-2 기관": "—"})
            st.dataframe(pd.DataFrame(debug_rows), use_container_width=True)
            st.caption("※ 네이버금융 frgn.naver 직접 파싱 실데이터")

        # ── 마스터 점수 계산 ──────────────────────────────────────────────────
        scored_rows = []
        for ticker, row in top15_base.iterrows():
            s = score_ticker(ticker, row, investor_map, news_map)
            scored_rows.append({
                "종목명":        row["종목명"],
                "섹터":          row["섹터"],
                "현재가":        row["현재가"],
                "등락률(%)":     row["등락률(%)"],
                "RSI":           row["RSI"],
                "눌림목신호":    row["눌림목신호"],
                "기관/연기금":   s["기관/연기금"],
                "숏스퀴즈":      s["숏스퀴즈"],
                "눌림목":        s["눌림목"],
                "뉴스호재":      s["뉴스호재"],
                "매수적합도(%)": s["매수적합도(%)"],
                "타점분석":      s["타점분석"],
                "수급신호":      s["수급신호"],
                "_squeeze":      s["폭발후보"],
                "_safepin":      s["안전핀"],
                "_기관당일":     s["_기관당일"],
                "_외국인당일":   s["_외국인당일"],
                "_기관연속일":   s["_기관연속일"],
            })

        ranked = (
            pd.DataFrame(scored_rows, index=top15_base.index)
            .sort_values("매수적합도(%)", ascending=False)
            .reset_index()
        )
        ranked.insert(0, "순위", range(1, len(ranked) + 1))

        # ── 표 스타일 ─────────────────────────────────────────────────────────
        def rank_bg(v):
            if v == 1:    return "background-color:#7c3aed;color:white;font-weight:bold"
            elif v <= 3:  return "background-color:#1e3a8a;color:white;font-weight:bold"
            elif v <= 7:  return "background-color:#1d4ed8;color:white"
            return ""

        def fit_color(v):
            if v >= 70:   return "color:#22c55e;font-weight:bold"
            elif v >= 50: return "color:#f59e0b;font-weight:bold"
            elif v >= 30: return "color:#94a3b8"
            return "color:#ef4444"

        def chg_color(v):
            if isinstance(v, (int, float)):
                if v < 0: return "color:#ef4444;font-weight:bold"
                if v > 0: return "color:#22c55e;font-weight:bold"
            return ""

        display = ["순위", "종목명", "현재가", "등락률(%)", "RSI",
                   "기관/연기금", "숏스퀴즈", "눌림목", "뉴스호재",
                   "매수적합도(%)", "눌림목신호"]

        styled = (
            ranked[display].style
            .map(rank_bg,   subset=["순위"])
            .map(fit_color, subset=["매수적합도(%)"])
            .map(chg_color, subset=["등락률(%)"])
            .format({
                "현재가":        "{:,}",
                "등락률(%)":     "{:+.2f}%",
                "기관/연기금":   "{:.0f}점",
                "숏스퀴즈":      "{:.0f}점",
                "눌림목":        "{:.1f}점",
                "뉴스호재":      "{:.0f}점",
                "매수적합도(%)": "{:.1f}%",
                "RSI":           "{:.1f}",
            })
        )
        st.dataframe(styled, use_container_width=True)

        # ── 타점 분석 한줄평 ──────────────────────────────────────────────────
        st.markdown("### 🎯 종목별 타점 분석 한줄평")
        for _, r in ranked.iterrows():
            badge = ""
            if r["_squeeze"]:  badge += " 💥폭발후보"
            if r["_safepin"]:  badge += " 🛡️안전핀"
            fit = r["매수적합도(%)"]
            bar_col = "#22c55e" if fit >= 70 else "#f59e0b" if fit >= 50 else "#94a3b8"
            # 기관/외국인 수급 원본 표시
            inst_raw = r["_기관당일"]
            frgn_raw = r["_외국인당일"]
            inst_txt = f"기관 {inst_raw:+,}" if inst_raw != 0 else "기관 데이터없음"
            frgn_txt = f"외국인 {frgn_raw:+,}" if frgn_raw != 0 else "외국인 데이터없음"
            st.markdown(
                f"**#{int(r['순위'])} {r['종목명']}**{badge} "
                f"<span style='color:{bar_col};font-weight:bold'>적합도 {fit:.1f}%</span> "
                f"<span style='color:#64748b;font-size:0.85em'>({inst_txt} | {frgn_txt})</span><br>"
                f"→ {r['타점분석']}",
                unsafe_allow_html=True,
            )

        # ── TOP 3 카드 ────────────────────────────────────────────────────────
        st.markdown("### 🥇 즉시 매수 후보 TOP 3")
        top3_cols = st.columns(3)
        medals    = ["🥇", "🥈", "🥉"]
        for i, (_, r) in enumerate(ranked.head(3).iterrows()):
            with top3_cols[i]:
                st.markdown(f"#### {medals[i]} {r['종목명']}")
                st.metric("현재가", f"{r['현재가']:,}원",
                          f"{r['등락률(%)']:+.2f}%",
                          delta_color="normal" if r["등락률(%)"] >= 0 else "inverse")
                st.progress(int(r["매수적합도(%)"]),
                            text=f"매수 적합도 {r['매수적합도(%)']:.1f}%")
                st.write(f"**수급신호**: {r['수급신호']}")
                st.write(f"**눌림목**: {r['눌림목신호']}")
                st.write(f"**타점**: {r['타점분석']}")

    else:
        st.info("위 버튼을 눌러 분석을 시작하세요.")


# ── TAB 2: 수급 분석표 ───────────────────────────────────────────────────────
with tab2:
    st.subheader(f"📊 {date_str} {market_type} 입체 수급 분석")
    _run_btn("btn2")

    result = st.session_state.get("result")
    if result is not None and not result.empty:
        top15 = result.sort_values(
            ["거래대금(억)", "거래량비율(%)"], ascending=False
        ).head(15)

        def chg_color2(v):
            if isinstance(v, (int, float)):
                if v < 0: return "color:#ef4444;font-weight:bold"
                if v > 0: return "color:#22c55e;font-weight:bold"
            return ""

        styled2 = (
            top15[["종목명", "섹터", "현재가", "등락률(%)",
                   "거래대금(억)", "거래량비율(%)", "RSI", "눌림목신호"]].style
            .background_gradient(subset=["거래대금(억)"],  cmap="Blues")
            .background_gradient(subset=["거래량비율(%)"], cmap="Oranges")
            .map(chg_color2, subset=["등락률(%)"])
            .format({
                "현재가":        "{:,}",
                "등락률(%)":     "{:+.2f}%",
                "거래대금(억)":  "{:,.1f}억",
                "거래량비율(%)": "{:.1f}%",
                "RSI":           "{:.1f}",
            })
        )
        st.dataframe(styled2, use_container_width=True)
        st.info("💡 거래대금: 당일 체결금액(억) | 거래량비율: 20일 평균 대비")
    else:
        st.info("위 버튼을 눌러 분석을 시작하세요.")


# ── TAB 3: 섹터 흐름 ─────────────────────────────────────────────────────────
with tab3:
    st.subheader("💰 섹터별 돈의 흐름")
    result = st.session_state.get("result")
    if result is not None and not result.empty:
        sector_df = get_sector_flow(result)
        top3_sec  = sector_df.head(3)
        sc = st.columns(3)
        for i, (_, row) in enumerate(top3_sec.iterrows()):
            with sc[i]:
                st.metric(f"{'🥇🥈🥉'[i]} {row['섹터']}",
                          f"{row['섹터 거래대금(억)']:,.1f}억",
                          f"비중 {row['비중(%)']:.1f}%")
        st.bar_chart(sector_df.set_index("섹터")["섹터 거래대금(억)"])
        st.dataframe(sector_df, use_container_width=True)
        if not top3_sec.empty:
            st.info(f"📡 자금 집중: **{top3_sec.iloc[0]['섹터']}** 섹터 — 해당 섹터 대장주 추가 수급 유입 모니터링.")
    else:
        st.info("수급 분석표 탭에서 먼저 분석을 실행하세요.")


# ── TAB 4: 한글 뉴스 ─────────────────────────────────────────────────────────
with tab4:
    st.subheader("📰 네이버 금융 — 한국어 뉴스 미반영 호재 분석")
    result = st.session_state.get("result")
    if result is not None and not result.empty:
        top15_n = result.sort_values(
            ["거래대금(억)", "거래량비율(%)"], ascending=False
        ).head(15)
        nm = get_news_batch(tuple(top15_n.index.tolist()))
        for ticker in top15_n.index:
            name = top15_n.loc[ticker, "종목명"]
            headlines = nm.get(ticker, [])
            hits = [kw for kw in NEWS_KEYWORDS if any(kw in h for h in headlines)]
            badge = f"  🔥 **호재 키워드: {', '.join(hits)}**" if hits else ""
            with st.expander(f"📌 {name} ({ticker}){badge}", expanded=bool(hits)):
                if headlines:
                    for h in headlines:
                        st.markdown(f"- {h}")
                    st.caption("※ 위 뉴스가 현재가에 미반영된 호재/악재일 수 있습니다.")
                else:
                    st.write("네이버 금융 뉴스를 가져오지 못했습니다.")
    else:
        st.info("수급 분석표 탭에서 먼저 분석을 실행하세요.")


# ── TAB 5: 오버행/블록딜 ─────────────────────────────────────────────────────
with tab5:
    st.subheader("⚠️ 오버행 / 블록딜 정밀 감지기")
    result = st.session_state.get("result")
    if result is not None and not result.empty:
        top15_oh = result.sort_values(
            ["거래대금(억)", "거래량비율(%)"], ascending=False
        ).head(15)
        hits = detect_overhang(top15_oh.index.tolist())

        st.markdown("#### 🔎 TOP 15 내 오버행 감지")
        if hits:
            for h in hits:
                t     = h["종목코드"]
                stocks = KOSPI_STOCKS if t in KOSPI_STOCKS else KOSDAQ_STOCKS
                name  = stocks[t][0] if t in stocks else t
                icon  = "🛡️" if h["safe"] else "⚠️"
                with st.expander(f"{icon} {name} ({t}) — {h['type']}", expanded=True):
                    st.markdown(f"**유형**: `{h['type']}`")
                    st.markdown(f"**분석**: {h['comment']}")
                    if h["safe"]:
                        st.success("→ 하방 경직성 확보 '안전핀' 역할 가능성 있음.")
                    else:
                        st.warning("→ 물량 출회 시 단기 주가 압박. 수급 이탈 즉각 손절 확인.")
        else:
            st.success("✅ TOP 15 내 즉각적 오버행 리스크 없음.")

        st.markdown("#### 📋 전체 오버행 모니터링")
        oh_rows = []
        for h in detect_overhang(list(OVERHANG_DB.keys())):
            t = h["종목코드"]
            s = KOSPI_STOCKS if t in KOSPI_STOCKS else KOSDAQ_STOCKS
            oh_rows.append({
                "종목명": s[t][0] if t in s else t, "코드": t,
                "유형":   h["type"],
                "안전핀": "✅ 하방경직" if h["safe"] else "❌ 물량주의",
                "분석":   h["comment"],
            })
        if oh_rows:
            st.dataframe(pd.DataFrame(oh_rows), use_container_width=True)
        st.info("💡 안전핀 ✅ = 오버행 있으나 하방 경직성 확보. ❌ = 물량 압박 주의.")
    else:
        st.info("수급 분석표 탭에서 먼저 분석을 실행하세요.")
