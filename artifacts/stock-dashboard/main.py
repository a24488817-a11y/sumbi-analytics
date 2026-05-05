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
# 종목 / 섹터 데이터베이스
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
    "042660": {"type": "블록딜(PRS)", "comment": "대형 블록딜이지만 전략적 투자자 유치 목적. 블록딜 후 하방 경직성 확보 '안전핀' 패턴 주목."},
    "003670": {"type": "CB 전환 잔액", "comment": "전환사채 전환 물량 출회 가능성. 단, 포스코그룹 지원 시 하방 지지선 역할."},
    "086520": {"type": "CB/블록딜",  "comment": "에코프로그룹 CB 물량 상존. 급등 시 차익실현 출회 주의."},
    "247540": {"type": "CB 전환",    "comment": "에코프로비엠 전환사채 물량 상존. 수급 급변 시 우선 점검 대상."},
    "028300": {"type": "유상증자",   "comment": "HLB 유상증자 후 물량 부담 잔존. 임상 이벤트가 상승 모멘텀으로 작용 시 상쇄 가능."},
    "196170": {"type": "BW 잔액",   "comment": "알테오젠 BW 잔액 존재. 기술수출 모멘텀으로 상쇄 기대."},
    "035720": {"type": "블록딜",     "comment": "카카오 주요 주주 블록딜 전례. 추가 블록딜 리스크 모니터링 권고."},
}

SUFFIX = {"KOSPI": ".KS", "KOSDAQ": ".KQ"}
NAVER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://finance.naver.com/",
}

# ───────────────────────────────────────────────────────────────────────────────
# 기술적 분석 함수
# ───────────────────────────────────────────────────────────────────────────────
def calc_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff().dropna()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs  = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not rsi.empty else 50.0


def calc_pullback_score(close_series: pd.Series, vol_series: pd.Series) -> dict:
    """
    눌림목 매수 타이밍 점수 (0~100).
    5일선·10일선·20일선 지지 반등 + RSI 저점 탈출 + 거래량 패턴으로 계산.
    """
    if len(close_series) < 25:
        return {"score": 0, "signal": "데이터 부족", "detail": {}}

    ma5  = close_series.rolling(5).mean()
    ma10 = close_series.rolling(10).mean()
    ma20 = close_series.rolling(20).mean()

    cur   = close_series.iloc[-1]
    prev  = close_series.iloc[-2]
    ma5c  = ma5.iloc[-1];  ma5p  = ma5.iloc[-2]
    ma10c = ma10.iloc[-1]; ma10p = ma10.iloc[-2]
    ma20c = ma20.iloc[-1]

    rsi = calc_rsi(close_series)

    avg_vol_20  = vol_series.tail(20).mean()
    avg_vol_3   = vol_series.tail(3).mean()
    vol_ratio_r = avg_vol_3 / avg_vol_20 if avg_vol_20 > 0 else 1.0

    # ── 점수 항목 ────────────────────────────────────────────────────
    score = 0
    detail = {}

    # 1) 5일선 지지 (골든존: 현재가가 MA5 ±1% 이내 or 위)
    ma5_gap = (cur - ma5c) / ma5c * 100
    if 0 <= ma5_gap <= 3:
        score += 25; detail["MA5"] = f"✅ 5일선 위 근접 (+{ma5_gap:.1f}%)"
    elif -1 <= ma5_gap < 0:
        score += 20; detail["MA5"] = f"🟡 5일선 하단 터치 ({ma5_gap:.1f}%) — 반등 주목"
    else:
        detail["MA5"] = f"❌ 5일선 이탈 ({ma5_gap:.1f}%)"

    # 2) 10일선 지지
    ma10_gap = (cur - ma10c) / ma10c * 100
    if 0 <= ma10_gap <= 5:
        score += 20; detail["MA10"] = f"✅ 10일선 위 근접 (+{ma10_gap:.1f}%)"
    elif -1.5 <= ma10_gap < 0:
        score += 15; detail["MA10"] = f"🟡 10일선 하단 터치 ({ma10_gap:.1f}%) — 지지선 확인"
    else:
        detail["MA10"] = f"❌ 10일선 이탈 ({ma10_gap:.1f}%)"

    # 3) 정배열 여부 (MA5 > MA10 > MA20)
    if ma5c > ma10c > ma20c:
        score += 15; detail["정배열"] = "✅ MA5>MA10>MA20 완전 정배열"
    elif ma5c > ma10c:
        score += 8;  detail["정배열"] = "🟡 MA5>MA10 부분 정배열"
    else:
        detail["정배열"] = "❌ 역배열 — 추세 주의"

    # 4) 눌림목 반등 확인 (전일 대비 양봉 전환)
    price_chg = (cur - prev) / prev * 100
    if price_chg > 0 and prev < ma5p:
        score += 20; detail["반등"] = f"✅ 눌림 후 양봉 반등 (+{price_chg:.1f}%) — 진입 타이밍"
    elif price_chg > 0:
        score += 10; detail["반등"] = f"🟡 상승 중 ({price_chg:.1f}%)"
    else:
        detail["반등"] = f"❌ 하락 중 ({price_chg:.1f}%)"

    # 5) RSI 저점 탈출 (30~50 구간이 최적 눌림목 매수 구간)
    if 30 <= rsi <= 50:
        score += 20; detail["RSI"] = f"✅ RSI {rsi:.1f} — 눌림목 최적 매수 구간"
    elif 50 < rsi <= 65:
        score += 10; detail["RSI"] = f"🟡 RSI {rsi:.1f} — 상승 중반"
    elif rsi < 30:
        score += 5;  detail["RSI"] = f"⚠️ RSI {rsi:.1f} — 과매도 (반등 기대, 추세 확인 필요)"
    else:
        detail["RSI"] = f"❌ RSI {rsi:.1f} — 과매수 구간"

    # 6) 거래량 패턴: 눌림 시 거래량 감소 → 반등 시 증가가 이상적
    if 0.5 <= vol_ratio_r <= 1.2:
        score += 0; detail["거래량패턴"] = f"🟡 최근 3일 거래량 정상 범위 (평균 대비 {vol_ratio_r:.1f}x)"
    elif vol_ratio_r > 1.2:
        score += 0; detail["거래량패턴"] = f"🔴 최근 3일 거래량 급증 ({vol_ratio_r:.1f}x) — 눌림 완료 or 고점 주의"
    else:
        score += 0; detail["거래량패턴"] = f"⚪ 거래량 감소 중 ({vol_ratio_r:.1f}x) — 눌림 진행 중"

    # 시그널 분류
    if score >= 75:
        signal = "🔴 즉시 매수 타이밍 (HIGH)"
    elif score >= 50:
        signal = "🟡 매수 준비 (MIDDLE)"
    elif score >= 30:
        signal = "⚪ 관망 (LOW)"
    else:
        signal = "❌ 진입 불가"

    return {"score": min(score, 100), "signal": signal, "detail": detail,
            "rsi": rsi, "ma5": ma5c, "ma10": ma10c, "ma20": ma20c}


# ───────────────────────────────────────────────────────────────────────────────
# 캐시 함수
# ───────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_macro_indices():
    symbols = {"KOSPI": "^KS11", "KOSDAQ": "^KQ11", "나스닥": "^IXIC", "나스닥선물": "NQ=F"}
    result = {}
    for name, sym in symbols.items():
        try:
            hist = yf.Ticker(sym).history(period="2d", interval="1d")
            if len(hist) >= 2:
                prev = hist["Close"].iloc[-2]; curr = hist["Close"].iloc[-1]
                chg = curr - prev; pct = chg / prev * 100
                result[name] = {"현재": curr, "변동": chg, "변동률": pct}
            elif len(hist) == 1:
                result[name] = {"현재": hist["Close"].iloc[-1], "변동": 0.0, "변동률": 0.0}
        except Exception:
            result[name] = None
    return result


@st.cache_data(ttl=300)
def get_pilsalgi_data(date_str, market):
    stocks = KOSPI_STOCKS if market == "KOSPI" else KOSDAQ_STOCKS
    suffix = SUFFIX[market]
    yf_tickers = [t + suffix for t in stocks.keys()]

    target_dt = datetime.strptime(date_str, "%Y%m%d")
    start_dt  = target_dt - timedelta(days=60)   # 눌림목 분석을 위해 60일치
    end_dt    = target_dt + timedelta(days=2)

    raw = yf.download(
        yf_tickers,
        start=start_dt.strftime("%Y-%m-%d"),
        end=end_dt.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
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

    # ── 눌림목 점수 계산 ────────────────────────────────────────────
    pb_scores, pb_signals, rsi_vals = [], [], []
    for t_suffix in close.columns:
        t = t_suffix.replace(suffix, "")
        try:
            c_s = close[t_suffix].dropna()
            v_s = volume[t_suffix].dropna()
            pb  = calc_pullback_score(c_s, v_s)
            pb_scores.append(pb["score"])
            pb_signals.append(pb["signal"])
            rsi_vals.append(round(pb.get("rsi", 50), 1))
        except Exception:
            pb_scores.append(0); pb_signals.append("N/A"); rsi_vals.append(50)

    result = pd.DataFrame({
        "현재가":       latest_close.round(0).astype("Int64"),
        "등락률(%)":    change_pct,
        "거래대금(억)": trading_value,
        "거래량비율(%)":vol_ratio,
    })
    result.index = [t.replace(suffix, "") for t in result.index]
    result.insert(0, "종목명",  [stocks[t][0] if t in stocks else t for t in result.index])
    result.insert(1, "섹터",    [stocks[t][1] if t in stocks else "기타" for t in result.index])
    result["눌림목점수"]  = pb_scores
    result["눌림목신호"]  = pb_signals
    result["RSI"]         = rsi_vals

    result = result.dropna(subset=["현재가", "거래대금(억)"])
    result = result[result["거래대금(억)"] > 0]
    return result, actual_date


@st.cache_data(ttl=300)
def calc_combined_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """수급강도 + 눌림목점수 합산 랭킹 시스템"""
    if df is None or df.empty:
        return df

    # 수급강도 점수 정규화 (0~100)
    def minmax(s):
        mn, mx = s.min(), s.max()
        return (s - mn) / (mx - mn) * 100 if mx > mn else pd.Series([50.0] * len(s), index=s.index)

    supply_score = (
        minmax(df["거래대금(억)"]) * 0.6 +
        minmax(df["거래량비율(%)"]) * 0.4
    )
    pullback_score = df["눌림목점수"].astype(float)

    # 최종 점수: 수급강도 50% + 눌림목 50%
    df = df.copy()
    df["수급강도점수"]  = supply_score.round(1)
    df["최종점수"]      = (supply_score * 0.5 + pullback_score * 0.5).round(1)
    df["순위"]          = df["최종점수"].rank(ascending=False, method="first").astype(int)
    df = df.sort_values("순위")
    return df


@st.cache_data(ttl=600)
def get_naver_news(ticker: str) -> list:
    """네이버 금융 한국어 뉴스 크롤링"""
    try:
        url = f"https://finance.naver.com/item/news_news.naver?code={ticker}&page=1&sm=title_entity_id.basic&clusterId="
        resp = requests.get(url, headers=NAVER_HEADERS, timeout=5)
        if resp.status_code != 200:
            return []
        resp.encoding = "euc-kr"
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select("table.type5 tr")
        news = []
        for row in rows:
            title_el = row.select_one("td.title a")
            date_el  = row.select_one("td.date")
            if title_el and date_el:
                title = title_el.get_text(strip=True)
                date  = date_el.get_text(strip=True)
                if title:
                    news.append(f"[{date}] {title}")
            if len(news) >= 5:
                break
        return news
    except Exception:
        return []


@st.cache_data(ttl=600)
def get_news_batch(tickers: tuple) -> dict:
    return {t: get_naver_news(t) for t in tickers}


@st.cache_data(ttl=300)
def get_sector_flow(df: pd.DataFrame):
    if df is None or df.empty:
        return pd.DataFrame()
    sector_df = (
        df.groupby("섹터")["거래대금(억)"]
        .sum().sort_values(ascending=False).reset_index()
        .rename(columns={"거래대금(억)": "섹터 거래대금(억)"})
    )
    sector_df["비중(%)"] = (sector_df["섹터 거래대금(억)"] / sector_df["섹터 거래대금(억)"].sum() * 100).round(1)
    return sector_df


def detect_overhang(tickers: list):
    return [{"종목코드": t, **OVERHANG_DB[t]} for t in tickers if t in OVERHANG_DB]


# ───────────────────────────────────────────────────────────────────────────────
# 헤더 & 매크로 티커 바
# ───────────────────────────────────────────────────────────────────────────────
st.title("🚀 42대 필살기 주식 분석 엔진 v1.0")
st.markdown("---")

macro = get_macro_indices()
macro_cols = st.columns(4)
for col, key in zip(macro_cols, ["KOSPI", "KOSDAQ", "나스닥", "나스닥선물"]):
    d = macro.get(key)
    with col:
        if d:
            st.metric(
                label=key,
                value=f"{d['현재']:,.2f}" if d['현재'] < 100_000 else f"{d['현재']:,.0f}",
                delta=f"{d['변동률']:+.2f}%",
            )
        else:
            st.metric(label=key, value="N/A")

def market_comment():
    lines = []
    kd = macro.get("KOSPI"); nd = macro.get("나스닥"); nfd = macro.get("나스닥선물")
    if kd:
        if kd["변동률"] > 0.5:
            lines.append(f"🟢 **국내 장세**: KOSPI {kd['변동률']:+.2f}% 강세 — 외국인/기관 순매수 우위 가능성 높음.")
        elif kd["변동률"] < -0.5:
            lines.append(f"🔴 **국내 장세**: KOSPI {kd['변동률']:+.2f}% 약세 — 프로그램 매도 또는 외국인 이탈 점검 필요.")
        else:
            lines.append(f"⚪ **국내 장세**: KOSPI {kd['변동률']:+.2f}% 보합권 — 관망세, 수급 이벤트 주시.")
    if nd:
        if nd["변동률"] > 0.5:
            lines.append(f"🟢 **글로벌 리스크온**: 나스닥 {nd['변동률']:+.2f}% 상승 — 반도체·성장주 수급 유리.")
        elif nd["변동률"] < -0.5:
            lines.append(f"🔴 **글로벌 리스크오프**: 나스닥 {nd['변동률']:+.2f}% 하락 — IT·바이오 수급 압박 경고.")
        else:
            lines.append(f"⚪ **글로벌**: 나스닥 보합권 — 방향성 불명확, 단기 스캘핑 주의.")
    if nfd:
        sign = "상승" if nfd["변동률"] >= 0 else "하락"
        lines.append(f"📡 **나스닥선물**: {nfd['변동률']:+.2f}% {sign} — 다음 장 개장 분위기 선반영.")
    return lines

with st.expander("📊 현재 장세 3줄 분석 (매크로 코멘트)", expanded=True):
    for c in market_comment():
        st.markdown(c)

st.markdown("---")

# ───────────────────────────────────────────────────────────────────────────────
# 사이드바
# ───────────────────────────────────────────────────────────────────────────────
st.sidebar.header("🔍 분석 필터 설정")
target_date  = st.sidebar.date_input("분석 기준일", datetime.now() - timedelta(days=1))
date_str     = target_date.strftime("%Y%m%d")
market_type  = st.sidebar.selectbox("시장 선택", ["KOSPI", "KOSDAQ"])

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 데이터 새로고침")
if st.sidebar.button("🔄 데이터 새로고침"):
    if st.session_state.get("analysis_run"):
        st.cache_data.clear(); st.rerun()
    else:
        st.sidebar.info("먼저 분석을 시작해 주세요.")

auto_refresh     = st.sidebar.toggle("자동 새로고침", value=False)
refresh_interval = 60
if auto_refresh:
    refresh_interval = st.sidebar.selectbox(
        "새로고침 주기",
        options=[30, 60, 120, 300],
        format_func=lambda x: f"{x}초" if x < 60 else f"{x // 60}분",
        index=1,
    )
if auto_refresh and st.session_state.get("analysis_run"):
    count = st_autorefresh(interval=refresh_interval * 1000, key="autorefresh")
    if count > 0:
        st.cache_data.clear()

# ───────────────────────────────────────────────────────────────────────────────
# 공통 데이터 페치 (탭 이전에 실행 — 모든 탭이 공유)
# ───────────────────────────────────────────────────────────────────────────────
if st.session_state.get("analysis_run"):
    with st.spinner("42대 필살기 매트릭스 연산 중 (0.1% 오차 배제)..."):
        _result, _actual_date = get_pilsalgi_data(date_str, market_type)
    if _result is not None and not _result.empty:
        st.session_state["result"]      = _result
        st.session_state["actual_date"] = _actual_date
    else:
        st.error(f"⚠️ {date_str}({market_type}) 데이터 없음 — 공휴일·주말이거나 시장 미개장일입니다. 날짜를 변경하세요.")
        st.session_state["result"]      = None
        st.session_state["actual_date"] = None

# ───────────────────────────────────────────────────────────────────────────────
# 탭
# ───────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 통합 랭킹 TOP 15",
    "📊 수급 분석표",
    "💰 섹터 돈의 흐름",
    "📰 미반영 뉴스 (한글)",
    "⚠️ 오버행/블록딜 감지",
])

# ── 공통: 분석 실행 버튼 ──────────────────────────────────────────────────────
def run_analysis_button(key: str):
    if st.button("🚀 42대 필살기 엔진 풀가동 분석 시작", key=key):
        st.session_state["analysis_run"] = True
        st.session_state["market"]  = market_type
        st.session_state["date"]    = date_str
        st.cache_data.clear()

# ── TAB 1: 통합 랭킹 ─────────────────────────────────────────────────────────
with tab1:
    st.subheader("🏆 수급강도 × 눌림목 통합 랭킹 TOP 15")
    st.caption("거래대금·거래량비율(수급강도 50%) + 5일/10일선 지지·RSI·반등 패턴(눌림목 50%) 합산 점수 기준")

    run_analysis_button("btn_tab1")

    result = st.session_state.get("result")
    if result is not None and not result.empty:
        ranked = calc_combined_ranking(result).head(15)

        # 순위 컬럼 색상
        def rank_color(v):
            if v <= 3:   return "background-color:#1e3a8a; color:white; font-weight:bold"
            elif v <= 7: return "background-color:#1d4ed8; color:white"
            else:        return ""

        def score_color(v):
            if v >= 75: return "color:#22c55e; font-weight:bold"
            elif v >= 50: return "color:#f59e0b; font-weight:bold"
            else:        return "color:#94a3b8"

        def chg_color(v):
            if isinstance(v, (int, float)) and v < 0: return "color:#ef4444; font-weight:bold"
            elif isinstance(v, (int, float)) and v > 0: return "color:#22c55e; font-weight:bold"
            return ""

        display_cols = ["순위", "종목명", "섹터", "현재가", "등락률(%)",
                        "거래대금(억)", "거래량비율(%)", "RSI",
                        "눌림목점수", "수급강도점수", "최종점수", "눌림목신호"]

        styled = (
            ranked[display_cols].style
            .map(rank_color,   subset=["순위"])
            .map(score_color,  subset=["최종점수", "눌림목점수"])
            .map(chg_color,    subset=["등락률(%)"])
            .format({
                "현재가":        "{:,}",
                "등락률(%)":     "{:+.2f}%",
                "거래대금(억)":  "{:,.1f}억",
                "거래량비율(%)": "{:.1f}%",
                "눌림목점수":    "{:.0f}",
                "수급강도점수":  "{:.0f}",
                "최종점수":      "{:.1f}",
                "RSI":           "{:.1f}",
            })
        )
        st.dataframe(styled, use_container_width=True)

        # TOP 3 카드
        st.markdown("### 🥇 즉시 매수 후보 TOP 3 — 정밀 분석 카드")
        top3_cols = st.columns(3)
        for i, (ticker, row) in enumerate(ranked.head(3).iterrows()):
            with top3_cols[i]:
                medals = ["🥇", "🥈", "🥉"]
                st.markdown(f"#### {medals[i]} {row['종목명']}")
                st.metric(
                    label=f"현재가",
                    value=f"{row['현재가']:,}원",
                    delta=f"{row['등락률(%)']:+.2f}%",
                    delta_color="normal" if row["등락률(%)"] >= 0 else "inverse",
                )
                st.progress(int(row["최종점수"]),
                            text=f"최종점수 {row['최종점수']:.0f}/100")
                st.write(f"**눌림목**: {row['눌림목신호']}")
                st.write(f"**섹터**: {row['섹터']}  |  **RSI**: {row['RSI']:.1f}")
                st.write(f"**거래대금**: {row['거래대금(억)']:,.1f}억  |  **거래량비율**: {row['거래량비율(%)']:.0f}%")
    else:
        st.info("위 버튼을 눌러 분석을 시작하세요.")

# ── TAB 2: 수급 분석표 ───────────────────────────────────────────────────────
with tab2:
    st.subheader(f"📊 {date_str} {market_type} 입체 수급 분석")
    run_analysis_button("btn_tab2")

    result = st.session_state.get("result")
    actual_date = st.session_state.get("actual_date")
    if result is not None and not result.empty:
        if actual_date and actual_date != target_date.strftime("%Y-%m-%d"):
            st.info(f"📅 요청일 데이터 없음 → 가장 최근 거래일 **{actual_date}** 기준")

        top15 = result.sort_values(by=["거래대금(억)", "거래량비율(%)"], ascending=False).head(15)
        st.success(f"✅ 분석 완료: {len(top15)}종목 추출")

        def chg_color(v):
            if isinstance(v, (int, float)) and v < 0: return "color:#ef4444;font-weight:bold"
            elif isinstance(v, (int, float)) and v > 0: return "color:#22c55e;font-weight:bold"
            return ""

        styled = (
            top15[["종목명","섹터","현재가","등락률(%)","거래대금(억)","거래량비율(%)","RSI","눌림목신호"]].style
            .background_gradient(subset=["거래대금(억)"], cmap="Blues")
            .background_gradient(subset=["거래량비율(%)"], cmap="Oranges")
            .map(chg_color, subset=["등락률(%)"])
            .format({
                "현재가":        "{:,}",
                "등락률(%)":     "{:+.2f}%",
                "거래대금(억)":  "{:,.1f}억",
                "거래량비율(%)": "{:.1f}%",
                "RSI":           "{:.1f}",
            })
        )
        st.dataframe(styled, use_container_width=True)
        st.info("💡 거래대금: 당일 체결금액(억) | 거래량비율: 20일 평균 대비 (높을수록 이상수급 신호)")

        if auto_refresh:
            st.caption(f"마지막 새로고침: {datetime.now().strftime('%H:%M:%S')} · 주기: {refresh_interval}초")
    else:
        st.info("위 버튼을 눌러 분석을 시작하세요.")

# ── TAB 3: 섹터 흐름 ─────────────────────────────────────────────────────────
with tab3:
    st.subheader("💰 섹터별 돈의 흐름 (센터 흐름)")
    result = st.session_state.get("result")
    if result is not None and not result.empty:
        sector_df = get_sector_flow(result)
        top3 = sector_df.head(3)
        s_cols = st.columns(3)
        for i, (_, row) in enumerate(top3.iterrows()):
            with s_cols[i]:
                st.metric(
                    label=f"{'🥇🥈🥉'[i]} {row['섹터']}",
                    value=f"{row['섹터 거래대금(억)']:,.1f}억",
                    delta=f"비중 {row['비중(%)']:.1f}%",
                )
        st.bar_chart(sector_df.set_index("섹터")["섹터 거래대금(억)"])
        st.dataframe(sector_df, use_container_width=True)
        if not top3.empty:
            st.info(f"📡 **센터 흐름**: 당일 시장 자금은 **{top3.iloc[0]['섹터']}** 섹터에 집중. 해당 섹터 대장주 추가 수급 유입 모니터링.")
    else:
        st.info("수급 분석표 탭에서 먼저 분석을 실행하세요.")

# ── TAB 4: 한글 뉴스 ─────────────────────────────────────────────────────────
with tab4:
    st.subheader("📰 네이버 금융 한국어 뉴스 — 미반영 호재 분석")
    result = st.session_state.get("result")
    if result is not None and not result.empty:
        ranked_news = calc_combined_ranking(result).head(15)
        ticker_list = tuple(ranked_news.index.tolist())
        name_map    = dict(zip(ranked_news.index, ranked_news["종목명"]))

        with st.spinner("네이버 금융 한국어 뉴스 수집 중..."):
            news_map = get_news_batch(ticker_list)

        for ticker in ticker_list:
            name      = name_map.get(ticker, ticker)
            headlines = news_map.get(ticker, [])
            rank_row  = ranked_news.loc[ticker] if ticker in ranked_news.index else None
            rank_num  = int(rank_row["순위"]) if rank_row is not None else "-"

            with st.expander(f"#{rank_num} 📌 {name} ({ticker}) — 미반영 뉴스 & 호재 분석", expanded=False):
                if headlines:
                    for h in headlines:
                        st.markdown(f"- {h}")
                    st.caption("※ 위 뉴스가 현재가에 미반영된 호재/악재일 수 있습니다. 이벤트 드리븐 전략 적용 시 참고하세요.")
                else:
                    st.write("네이버 금융에서 최신 뉴스를 가져오지 못했습니다. (일시적 네트워크 문제 또는 종목 미지원)")
    else:
        st.info("수급 분석표 탭에서 먼저 분석을 실행하세요.")

# ── TAB 5: 오버행/블록딜 ─────────────────────────────────────────────────────
with tab5:
    st.subheader("⚠️ 오버행 / 블록딜 정밀 감지기")
    result = st.session_state.get("result")
    if result is not None and not result.empty:
        ranked_oh = calc_combined_ranking(result).head(15)
        hits = detect_overhang(ranked_oh.index.tolist())

        st.markdown("#### 🔎 TOP 15 내 오버행 감지")
        if hits:
            for h in hits:
                ticker  = h["종목코드"]
                stocks  = KOSPI_STOCKS if ticker in KOSPI_STOCKS else KOSDAQ_STOCKS
                name    = stocks[ticker][0] if ticker in stocks else ticker
                is_safe = any(k in h["comment"] for k in ["안전핀", "하방 경직", "지원", "상쇄"])
                icon    = "🛡️" if is_safe else "⚠️"
                with st.expander(f"{icon} {name} ({ticker}) — {h['type']}", expanded=True):
                    st.markdown(f"**물량 유형**: `{h['type']}`")
                    st.markdown(f"**분석 코멘트**: {h['comment']}")
                    if is_safe:
                        st.success("→ 블록딜/CB가 하방 경직성(안전핀) 역할 가능성 있음.")
                    else:
                        st.warning("→ 물량 출회 시 단기 주가 압박 가능. 수급 이탈 즉각 손절 라인 확인.")
        else:
            st.success("✅ TOP 15 내 즉각적 오버행/블록딜 리스크 감지 없음.")

        st.markdown("#### 📋 전체 오버행 모니터링 목록")
        all_hits = detect_overhang(list(OVERHANG_DB.keys()))
        rows = []
        for h in all_hits:
            t = h["종목코드"]
            s = KOSPI_STOCKS if t in KOSPI_STOCKS else KOSDAQ_STOCKS
            rows.append({"종목명": s[t][0] if t in s else t, "종목코드": t, "유형": h["type"], "분석": h["comment"]})
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

        st.info("💡 CB·BW 전환 → 주가 희석 압력 / 블록딜(PRS) → 대량 물량 단기 출회 위험. 단, 전략적 투자자 유치·그룹 지원 시 '안전핀(하방 지지선)' 역할 전환 가능.")
    else:
        st.info("수급 분석표 탭에서 먼저 분석을 실행하세요.")
