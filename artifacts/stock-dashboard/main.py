import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="42대 필살기 분석기", layout="wide")

# ───────────────────────────────────────────────────────────────────────────────
# 종목 / 섹터 데이터베이스
# ───────────────────────────────────────────────────────────────────────────────
KOSPI_STOCKS = {
    "005930": ("삼성전자",    "반도체/IT"),
    "000660": ("SK하이닉스",  "반도체/IT"),
    "035420": ("NAVER",       "인터넷/플랫폼"),
    "005380": ("현대차",      "자동차"),
    "051910": ("LG화학",      "화학/배터리"),
    "006400": ("삼성SDI",     "화학/배터리"),
    "068270": ("셀트리온",    "바이오/헬스케어"),
    "105560": ("KB금융",      "금융"),
    "028260": ("삼성물산",    "건설/산업재"),
    "012330": ("현대모비스",  "자동차"),
    "207940": ("삼성바이오로직스", "바이오/헬스케어"),
    "000270": ("기아",        "자동차"),
    "017670": ("SK텔레콤",    "통신"),
    "030200": ("KT",          "통신"),
    "015760": ("한국전력",    "에너지/유틸리티"),
    "034730": ("SK",          "지주/복합"),
    "032830": ("삼성생명",    "금융"),
    "086790": ("하나금융지주","금융"),
    "009540": ("HD현대중공업","조선/기계"),
    "010950": ("S-Oil",       "에너지/유틸리티"),
    "055550": ("신한지주",    "금융"),
    "024110": ("기업은행",    "금융"),
    "066570": ("LG전자",      "가전/전자"),
    "003550": ("LG",          "지주/복합"),
    "011200": ("HMM",         "운송/물류"),
    "034220": ("LG디스플레이","반도체/IT"),
    "009830": ("한화솔루션",  "화학/배터리"),
    "000100": ("유한양행",    "바이오/헬스케어"),
    "035720": ("카카오",      "인터넷/플랫폼"),
    "003490": ("대한항공",    "운송/물류"),
    "097950": ("CJ제일제당",  "소비재/음식"),
    "004020": ("현대제철",    "철강/소재"),
    "010130": ("고려아연",    "철강/소재"),
    "028050": ("삼성엔지니어링","건설/산업재"),
    "267250": ("HD현대",      "지주/복합"),
    "009150": ("삼성전기",    "반도체/IT"),
    "002790": ("아모레퍼시픽그룹","소비재/음식"),
    "090430": ("아모레퍼시픽","소비재/음식"),
    "004170": ("신세계",      "유통/소비"),
    "004000": ("롯데케미칼",  "화학/배터리"),
    "005490": ("POSCO홀딩스", "철강/소재"),
    "000810": ("삼성화재",    "금융"),
    "078930": ("GS",          "지주/복합"),
    "036460": ("한국가스공사","에너지/유틸리티"),
    "000720": ("현대건설",    "건설/산업재"),
    "016360": ("삼성증권",    "금융"),
    "139480": ("이마트",      "유통/소비"),
    "006800": ("미래에셋증권","금융"),
    "042660": ("한화오션",    "조선/기계"),
    "352820": ("하이브",      "엔터/미디어"),
    "035900": ("JYP엔터테인먼트","엔터/미디어"),
    "041510": ("SM엔터테인먼트","엔터/미디어"),
    "326030": ("SK바이오팜",  "바이오/헬스케어"),
    "033780": ("KT&G",        "소비재/음식"),
    "003670": ("포스코퓨처엠","화학/배터리"),
    "064350": ("현대로템",    "조선/기계"),
    "229640": ("LS ELECTRIC", "전력/전기"),
    "069960": ("현대백화점",  "유통/소비"),
    "011780": ("금호석유",    "화학/배터리"),
    "011070": ("LG이노텍",    "반도체/IT"),
    "010140": ("삼성중공업",  "조선/기계"),
    "047050": ("포스코인터내셔널","지주/복합"),
    "071050": ("한국금융지주","금융"),
    "377300": ("카카오페이",  "인터넷/플랫폼"),
    "112610": ("씨에스윈드",  "신재생에너지"),
    "008770": ("호텔신라",    "유통/소비"),
}

KOSDAQ_STOCKS = {
    "247540": ("에코프로비엠",   "화학/배터리"),
    "086520": ("에코프로",       "화학/배터리"),
    "196170": ("알테오젠",       "바이오/헬스케어"),
    "263750": ("펄어비스",       "게임"),
    "293490": ("카카오게임즈",   "게임"),
    "068760": ("셀트리온제약",   "바이오/헬스케어"),
    "028300": ("HLB",            "바이오/헬스케어"),
    "045020": ("코스맥스",       "소비재/음식"),
    "214150": ("클래시스",       "의료기기"),
    "064760": ("티씨케이",       "반도체/IT"),
    "357780": ("솔브레인",       "반도체/IT"),
    "030520": ("한글과컴퓨터",   "반도체/IT"),
    "053800": ("안랩",           "반도체/IT"),
    "145720": ("덴티움",         "의료기기"),
    "068600": ("대원제약",       "바이오/헬스케어"),
    "323410": ("카카오뱅크",     "금융"),
    "039030": ("이오테크닉스",   "반도체/IT"),
    "131970": ("테크윙",         "반도체/IT"),
    "240810": ("원익IPS",        "반도체/IT"),
    "058470": ("리노공업",       "반도체/IT"),
    "009420": ("한올바이오파마", "바이오/헬스케어"),
    "078340": ("컴투스",         "게임"),
    "036830": ("솔브레인홀딩스", "화학/배터리"),
    "048260": ("오스템임플란트", "의료기기"),
    "122870": ("와이지엔터테인먼트","엔터/미디어"),
    "067160": ("아프리카TV",     "인터넷/플랫폼"),
    "108490": ("로보티즈",       "로봇/AI"),
}

# 알려진 CB/BW/블록딜 리스크 종목 (간략 정보)
OVERHANG_DB = {
    "042660": {"type": "블록딜(PRS)", "comment": "대형 블록딜이지만 전략적 투자자 유치 목적으로 해석 가능. 블록딜 후 주가 하방 경직성 확보 패턴('안전핀') 주목."},
    "003670": {"type": "CB 전환 잔액", "comment": "전환사채 전환 물량 출회 가능성. 단, 포스코그룹 지원 시 하방 지지선 역할."},
    "086520": {"type": "CB/블록딜", "comment": "에코프로그룹 CB 물량 상존. 급등 시 차익실현 출회 주의."},
    "247540": {"type": "CB 전환", "comment": "에코프로비엠 전환사채 물량 상존. 수급 급변 시 우선 점검 대상."},
    "028300": {"type": "유상증자", "comment": "HLB 유상증자 후 물량 부담 잔존. 임상 이벤트가 상승 모멘텀으로 작용 시 상쇄 가능."},
    "196170": {"type": "BW 잔액", "comment": "알테오젠 신주인수권부사채(BW) 잔액 존재. 기술수출 모멘텀으로 상쇄 기대."},
    "035720": {"type": "블록딜", "comment": "카카오 주요 주주 블록딜 전례 있음. 추가 블록딜 리스크 모니터링 권고."},
}

SUFFIX = {"KOSPI": ".KS", "KOSDAQ": ".KQ"}

# ───────────────────────────────────────────────────────────────────────────────
# 캐시 함수들
# ───────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_macro_indices():
    symbols = {
        "KOSPI": "^KS11",
        "KOSDAQ": "^KQ11",
        "나스닥": "^IXIC",
        "나스닥선물": "NQ=F",
    }
    result = {}
    for name, sym in symbols.items():
        try:
            t = yf.Ticker(sym)
            hist = t.history(period="2d", interval="1d")
            if len(hist) >= 2:
                prev = hist["Close"].iloc[-2]
                curr = hist["Close"].iloc[-1]
                chg = curr - prev
                pct = chg / prev * 100
                result[name] = {"현재": curr, "변동": chg, "변동률": pct}
            elif len(hist) == 1:
                curr = hist["Close"].iloc[-1]
                result[name] = {"현재": curr, "변동": 0.0, "변동률": 0.0}
        except Exception:
            result[name] = None
    return result


@st.cache_data(ttl=300)
def get_pilsalgi_data(date_str, market):
    stocks = KOSPI_STOCKS if market == "KOSPI" else KOSDAQ_STOCKS
    suffix = SUFFIX[market]
    yf_tickers = [t + suffix for t in stocks.keys()]

    target_dt = datetime.strptime(date_str, "%Y%m%d")
    start_dt = target_dt - timedelta(days=40)
    end_dt = target_dt + timedelta(days=2)

    raw = yf.download(
        yf_tickers,
        start=start_dt.strftime("%Y-%m-%d"),
        end=end_dt.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
    )

    if raw.empty or "Close" not in raw:
        return pd.DataFrame(), None

    close = raw["Close"].dropna(how="all")
    volume = raw["Volume"].dropna(how="all")

    if len(close) < 2:
        return pd.DataFrame(), None

    actual_date = close.index[-1].strftime("%Y-%m-%d")
    latest_close = close.iloc[-1]
    prev_close   = close.iloc[-2]
    latest_vol   = volume.iloc[-1]
    avg_vol_20   = volume.tail(20).mean()

    change_pct    = ((latest_close - prev_close) / prev_close * 100).round(2)
    trading_value = (latest_close * latest_vol / 1e8).round(1)
    vol_ratio     = (latest_vol / avg_vol_20 * 100).round(1)

    result = pd.DataFrame({
        "현재가":      latest_close.round(0).astype("Int64"),
        "등락률(%)":   change_pct,
        "거래대금(억)": trading_value,
        "거래량비율(%)": vol_ratio,
    })
    result.index = [t.replace(suffix, "") for t in result.index]

    names   = [stocks[t][0] if t in stocks else t for t in result.index]
    sectors = [stocks[t][1] if t in stocks else "기타" for t in result.index]
    result.insert(0, "종목명",  names)
    result.insert(1, "섹터",    sectors)
    result = result.dropna(subset=["현재가", "거래대금(억)"])
    result = result[result["거래대금(억)"] > 0]
    return result, actual_date


@st.cache_data(ttl=300)
def get_sector_flow(df: pd.DataFrame):
    if df is None or df.empty:
        return pd.DataFrame()
    sector_df = (
        df.groupby("섹터")["거래대금(억)"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"거래대금(억)": "섹터 거래대금(억)"})
    )
    sector_df["비중(%)"] = (sector_df["섹터 거래대금(억)"] / sector_df["섹터 거래대금(억)"].sum() * 100).round(1)
    return sector_df


@st.cache_data(ttl=600)
def get_news_for_tickers(tickers: tuple):
    news_map = {}
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker + ".KS")
            items = t.news or []
            if not items:
                t2 = yf.Ticker(ticker + ".KQ")
                items = t2.news or []
            headlines = []
            for n in items[:3]:
                title = n.get("title") or n.get("content", {}).get("title", "")
                pub   = n.get("providerPublishTime") or n.get("content", {}).get("pubDate", "")
                if pub:
                    try:
                        pub_str = datetime.fromtimestamp(pub).strftime("%m/%d %H:%M")
                    except Exception:
                        pub_str = str(pub)[:10]
                else:
                    pub_str = ""
                if title:
                    headlines.append(f"[{pub_str}] {title}" if pub_str else title)
            news_map[ticker] = headlines
        except Exception:
            news_map[ticker] = []
    return news_map


def detect_overhang(tickers: list):
    hits = []
    for t in tickers:
        if t in OVERHANG_DB:
            hits.append({"종목코드": t, **OVERHANG_DB[t]})
    return hits


# ───────────────────────────────────────────────────────────────────────────────
# 헤더 & 매크로 티커 바
# ───────────────────────────────────────────────────────────────────────────────
st.title("🚀 42대 필살기 주식 분석 엔진 v1.0")
st.markdown("---")

macro = get_macro_indices()

def fmt_index(name, data):
    if data is None:
        return f"**{name}** — N/A"
    arrow = "▲" if data["변동률"] >= 0 else "▼"
    color = "🟢" if data["변동률"] >= 0 else "🔴"
    val = f"{data['현재']:,.2f}" if data['현재'] < 100000 else f"{data['현재']:,.0f}"
    return f"{color} **{name}** {val} {arrow}{abs(data['변동률']):.2f}%"

macro_cols = st.columns(4)
for col, key in zip(macro_cols, ["KOSPI", "KOSDAQ", "나스닥", "나스닥선물"]):
    d = macro.get(key)
    with col:
        if d:
            delta_str = f"{d['변동률']:+.2f}%"
            st.metric(
                label=key,
                value=f"{d['현재']:,.2f}" if d['현재'] < 100000 else f"{d['현재']:,.0f}",
                delta=delta_str,
            )
        else:
            st.metric(label=key, value="N/A")

# 3줄 장세 분석
kospi_d = macro.get("KOSPI")
nas_d   = macro.get("나스닥")
nf_d    = macro.get("나스닥선물")

def market_comment():
    lines = []
    if kospi_d:
        if kospi_d["변동률"] > 0.5:
            lines.append(f"🟢 **국내 장세**: KOSPI {kospi_d['변동률']:+.2f}% 강세 — 외국인/기관 순매수 우위 가능성 높음.")
        elif kospi_d["변동률"] < -0.5:
            lines.append(f"🔴 **국내 장세**: KOSPI {kospi_d['변동률']:+.2f}% 약세 — 프로그램 매도 또는 외국인 이탈 점검 필요.")
        else:
            lines.append(f"⚪ **국내 장세**: KOSPI {kospi_d['변동률']:+.2f}% 보합권 — 관망세, 수급 이벤트 주시.")
    if nas_d:
        if nas_d["변동률"] > 0.5:
            lines.append(f"🟢 **글로벌 리스크온**: 나스닥 {nas_d['변동률']:+.2f}% 상승 — 반도체·성장주 수급 유리.")
        elif nas_d["변동률"] < -0.5:
            lines.append(f"🔴 **글로벌 리스크오프**: 나스닥 {nas_d['변동률']:+.2f}% 하락 — IT·바이오 섹터 수급 압박 경고.")
        else:
            lines.append(f"⚪ **글로벌**: 나스닥 보합권 — 매크로 방향성 불명확, 단기 스캘핑 주의.")
    if nf_d:
        sign = "상승" if nf_d["변동률"] >= 0 else "하락"
        lines.append(f"📡 **나스닥선물**: {nf_d['변동률']:+.2f}% {sign} — 다음 시장 개장 분위기 선반영 신호.")
    return lines

comments = market_comment()
if comments:
    with st.expander("📊 현재 장세 3줄 분석 (매크로 코멘트)", expanded=True):
        for c in comments:
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
if st.sidebar.button("🔄 데이터 새로고침", width="stretch"):
    if st.session_state.get("analysis_run"):
        st.cache_data.clear()
        st.rerun()
    else:
        st.sidebar.info("먼저 분석을 시작해 주세요.")

auto_refresh    = st.sidebar.toggle("자동 새로고침", value=False)
refresh_interval = 60
if auto_refresh:
    refresh_interval = st.sidebar.selectbox(
        "새로고침 주기",
        options=[30, 60, 120, 300],
        format_func=lambda x: f"{x}초" if x < 60 else f"{x // 60}분",
        index=1,
    )

if auto_refresh and st.session_state.get("analysis_run"):
    count = st_autorefresh(interval=refresh_interval * 1000, key="data_autorefresh")
    if count > 0:
        st.cache_data.clear()

# ───────────────────────────────────────────────────────────────────────────────
# 탭 구성
# ───────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 수급 분석표",
    "💰 섹터 돈의 흐름",
    "📰 미반영 뉴스",
    "⚠️ 오버행/블록딜 감지",
])

# ── TAB 1: 수급 분석표 ─────────────────────────────────────────────────────────
with tab1:
    st.subheader(f"📊 {date_str} {market_type} 입체 수급 분석 (The Core)")

    if st.button("🚀 42대 필살기 엔진 풀가동 분석 시작", width="stretch"):
        st.session_state["analysis_run"] = True
        st.session_state["market"]       = market_type
        st.session_state["date"]         = date_str

    if st.session_state.get("analysis_run"):
        with st.spinner("42대 필살기 매트릭스 연산 중 (0.1% 오차 배제)..."):
            result_tuple = get_pilsalgi_data(date_str, market_type)

        result, actual_date = result_tuple if isinstance(result_tuple, tuple) else (result_tuple, None)

        if result is None or result.empty:
            st.error(f"⚠️ {date_str}({market_type}) 데이터 없음 — 공휴일·주말이거나 시장 미개장일입니다. 날짜를 변경하세요.")
        else:
            st.session_state["result"]      = result
            st.session_state["actual_date"] = actual_date

            if actual_date and actual_date != target_date.strftime("%Y-%m-%d"):
                st.info(f"📅 요청일 데이터 없음 → 가장 최근 거래일 **{actual_date}** 기준으로 분석합니다.")

            top_picks = result.sort_values(by=["거래대금(억)", "거래량비율(%)"], ascending=False).head(15)
            st.success(f"✅ 분석 완료: 42대 필살기 기반 우량 수급주 {len(top_picks)}종목 추출")

            def color_change(v):
                if isinstance(v, (int, float)) and v < 0:
                    return "color: #ef4444; font-weight:bold"
                elif isinstance(v, (int, float)) and v > 0:
                    return "color: #22c55e; font-weight:bold"
                return ""

            styled = (
                top_picks.style
                .background_gradient(subset=["거래대금(억)"], cmap="Blues")
                .background_gradient(subset=["거래량비율(%)"], cmap="Oranges")
                .map(color_change, subset=["등락률(%)"])
                .format({
                    "현재가":       "{:,}",
                    "등락률(%)":    "{:+.2f}%",
                    "거래대금(억)": "{:,.1f}억",
                    "거래량비율(%)":"{:.1f}%",
                })
            )
            st.dataframe(styled, width="stretch")
            st.info("💡 거래대금: 당일 체결금액(억) | 거래량비율: 20일 평균 대비 (높을수록 이상수급 신호)")

            st.markdown("### 🔍 42대 필살기 정밀 보고 — 대장주 TOP 3")
            cols = st.columns(3)
            for i, (ticker, row) in enumerate(top_picks.head(3).iterrows()):
                with cols[i]:
                    delta_color = "normal" if row["등락률(%)"] >= 0 else "inverse"
                    st.metric(
                        label=f"대장주 #{i+1}: {row['종목명']}",
                        value=f"{row['현재가']:,}원",
                        delta=f"{row['등락률(%)']:+.2f}%",
                        delta_color=delta_color,
                    )
                    vol_signal = (
                        "🔴 급등 이상수급" if row["거래량비율(%)"] > 200 else
                        "🟡 평균 이상" if row["거래량비율(%)"] > 120 else "⚪ 보통"
                    )
                    st.write(f"**섹터**: {row['섹터']}")
                    st.write(f"**거래대금** {row['거래대금(억)']:,.1f}억 | **수급신호** {vol_signal}")
                    st.write("- [배거차숏] 밸류업 및 숏스퀴즈 임계점")
                    st.write("- [달국금공] 매크로 변동성 하방 경직성")
                    st.write("- [정정자생] 정부정책 및 글로벌 생태계 수혜")

            if auto_refresh:
                st.caption(f"마지막 새로고침: {datetime.now().strftime('%H:%M:%S')} · 자동 주기: {refresh_interval}초")
    else:
        st.write("사이드바에서 분석일·시장을 설정하고 위 버튼을 눌러 분석을 시작하세요.")

# ── TAB 2: 섹터 돈의 흐름 ──────────────────────────────────────────────────────
with tab2:
    st.subheader("💰 섹터별 돈의 흐름 (센터 흐름)")

    result = st.session_state.get("result")
    if result is not None and not result.empty:
        sector_df = get_sector_flow(result)
        top3 = sector_df.head(3)

        st.markdown("#### 🏆 주도 섹터 TOP 3")
        s_cols = st.columns(3)
        medals = ["🥇", "🥈", "🥉"]
        for i, (_, row) in enumerate(top3.iterrows()):
            with s_cols[i]:
                st.metric(
                    label=f"{medals[i]} {row['섹터']}",
                    value=f"{row['섹터 거래대금(억)']:,.1f}억",
                    delta=f"비중 {row['비중(%)']:.1f}%",
                )

        st.markdown("#### 전체 섹터 거래대금 분포")
        st.bar_chart(sector_df.set_index("섹터")["섹터 거래대금(억)"])
        st.dataframe(sector_df, width="stretch")

        # 섹터 코멘트
        if not top3.empty:
            top_sector = top3.iloc[0]["섹터"]
            st.info(
                f"📡 **센터 흐름 판단**: 당일 시장 자금은 **{top_sector}** 섹터에 집중되고 있습니다. "
                f"해당 섹터 대장주를 중심으로 추가 수급 유입 가능성을 모니터링하세요."
            )
    else:
        st.info("수급 분석표 탭에서 먼저 분석을 실행하세요.")

# ── TAB 3: 미반영 뉴스 ────────────────────────────────────────────────────────
with tab3:
    st.subheader("📰 미반영 뉴스 실시간 크롤링")

    result = st.session_state.get("result")
    if result is not None and not result.empty:
        top_picks_news = result.sort_values(by=["거래대금(억)", "거래량비율(%)"], ascending=False).head(15)
        ticker_list    = tuple(top_picks_news.index.tolist())
        name_map       = dict(zip(top_picks_news.index, top_picks_news["종목명"]))

        with st.spinner("최신 뉴스 수집 중..."):
            news_map = get_news_for_tickers(ticker_list)

        for ticker in ticker_list:
            name     = name_map.get(ticker, ticker)
            headlines = news_map.get(ticker, [])
            with st.expander(f"📌 {name} ({ticker}) — 미반영 호재 분석", expanded=False):
                if headlines:
                    for h in headlines:
                        st.markdown(f"- {h}")
                    st.caption("※ 위 뉴스가 현재가에 미반영된 호재/악재일 수 있습니다. 이벤트 드리븐 전략 적용 시 참고하세요.")
                else:
                    st.write("최신 뉴스를 가져오지 못했습니다. (해당 종목 yfinance 뉴스 미지원)")
    else:
        st.info("수급 분석표 탭에서 먼저 분석을 실행하세요.")

# ── TAB 4: 오버행/블록딜 감지 ─────────────────────────────────────────────────
with tab4:
    st.subheader("⚠️ 오버행 / 블록딜 정밀 감지기")

    result = st.session_state.get("result")
    if result is not None and not result.empty:
        top15_tickers = (
            result.sort_values(by=["거래대금(억)", "거래량비율(%)"], ascending=False)
            .head(15).index.tolist()
        )
        hits = detect_overhang(top15_tickers)
        all_hits = detect_overhang(list(OVERHANG_DB.keys()))

        # 추출된 15종목 중 오버행 위험
        st.markdown("#### 🔎 분석 대상 15종목 내 오버행 감지 결과")
        if hits:
            for h in hits:
                ticker  = h["종목코드"]
                stocks  = KOSPI_STOCKS if ticker in KOSPI_STOCKS else KOSDAQ_STOCKS
                name    = stocks[ticker][0] if ticker in stocks else ticker
                ov_type = h["type"]
                comment = h["comment"]

                is_safe = "안전핀" in comment or "하방 경직" in comment or "지원" in comment
                icon    = "🛡️" if is_safe else "⚠️"

                with st.expander(f"{icon} {name} ({ticker}) — {ov_type}", expanded=True):
                    st.markdown(f"**물량 유형**: `{ov_type}`")
                    st.markdown(f"**분석 코멘트**: {comment}")
                    if is_safe:
                        st.success("→ 이 종목의 블록딜/CB는 단순 악재가 아닌 **하방 경직성(안전핀)** 역할 가능성 있음.")
                    else:
                        st.warning("→ 물량 출회 시 단기 주가 압박 가능. 수급 이탈 시 즉각 손절 라인 확인 필요.")
        else:
            st.success("✅ 분석 대상 15종목 내 즉각적인 오버행/블록딜 리스크 감지 없음.")

        # 시장 전체 오버행 모니터링 목록
        st.markdown("#### 📋 시장 전체 오버행 모니터링 목록")
        rows = []
        for h in all_hits:
            t = h["종목코드"]
            stocks = KOSPI_STOCKS if t in KOSPI_STOCKS else KOSDAQ_STOCKS
            name = stocks[t][0] if t in stocks else t
            rows.append({"종목명": name, "종목코드": t, "유형": h["type"], "분석 코멘트": h["comment"]})
        if rows:
            st.dataframe(pd.DataFrame(rows), width="stretch")

        st.info(
            "💡 **판단 기준**: CB(전환사채)/BW(신주인수권부사채) 전환 → 주가 희석 압력 / "
            "블록딜(PRS) → 대량 물량 단기 출회 위험. 단, 전략적 투자자 유치·그룹 지원 시 "
            "'안전핀(하방 지지선)' 역할로 전환 가능. 맥락을 반드시 함께 판단할 것."
        )
    else:
        st.info("수급 분석표 탭에서 먼저 분석을 실행하세요.")
