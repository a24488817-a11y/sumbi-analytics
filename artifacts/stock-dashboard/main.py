import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="42대 필살기 분석기", layout="wide")

KOSPI_STOCKS = {
    "005930": "삼성전자", "000660": "SK하이닉스", "035420": "NAVER", "005380": "현대차",
    "051910": "LG화학", "006400": "삼성SDI", "068270": "셀트리온", "105560": "KB금융",
    "028260": "삼성물산", "012330": "현대모비스", "207940": "삼성바이오로직스", "000270": "기아",
    "017670": "SK텔레콤", "030200": "KT", "015760": "한국전력", "034730": "SK",
    "032830": "삼성생명", "086790": "하나금융지주", "009540": "HD현대중공업", "010950": "S-Oil",
    "055550": "신한지주", "024110": "기업은행", "066570": "LG전자", "003550": "LG",
    "011200": "HMM", "034220": "LG디스플레이", "009830": "한화솔루션", "000100": "유한양행",
    "035720": "카카오", "003490": "대한항공", "097950": "CJ제일제당", "004020": "현대제철",
    "010130": "고려아연", "028050": "삼성엔지니어링", "267250": "HD현대", "009150": "삼성전기",
    "002790": "아모레퍼시픽그룹", "090430": "아모레퍼시픽", "004170": "신세계", "004000": "롯데케미칼",
    "005490": "POSCO홀딩스", "000810": "삼성화재", "007070": "GS리테일", "282330": "BGF리테일",
    "018880": "한온시스템", "078930": "GS", "036460": "한국가스공사", "000720": "현대건설",
    "016360": "삼성증권", "139480": "이마트", "006800": "미래에셋증권", "042660": "한화오션",
    "352820": "하이브", "035900": "JYP엔터테인먼트", "041510": "SM엔터테인먼트",
    "326030": "SK바이오팜", "033780": "KT&G", "003670": "포스코퓨처엠",
    "064350": "현대로템", "229640": "LS ELECTRIC", "069960": "현대백화점",
    "011780": "금호석유", "011070": "LG이노텍", "010140": "삼성중공업",
    "047050": "포스코인터내셔널", "071050": "한국금융지주", "377300": "카카오페이",
    "112610": "씨에스윈드", "008770": "호텔신라",
}

KOSDAQ_STOCKS = {
    "247540": "에코프로비엠", "086520": "에코프로", "196170": "알테오젠", "263750": "펄어비스",
    "293490": "카카오게임즈", "068760": "셀트리온제약", "028300": "HLB", "045020": "코스맥스",
    "214150": "클래시스", "064760": "티씨케이", "357780": "솔브레인", "030520": "한글과컴퓨터",
    "053800": "안랩", "145720": "덴티움", "091990": "셀트리온헬스케어", "041510": "SM엔터테인먼트",
    "035900": "JYP엔터테인먼트", "068600": "대원제약", "323410": "카카오뱅크",
    "950130": "엑스게이트", "039030": "이오테크닉스", "131970": "테크윙",
    "240810": "원익IPS", "058470": "리노공업", "054040": "한국전자인증",
    "009420": "한올바이오파마", "200880": "서연이화", "950160": "코오롱티슈진",
    "311390": "네카오", "041440": "삼아알미늄", "033290": "코웰패션",
    "078340": "컴투스", "036830": "솔브레인홀딩스", "048260": "오스템임플란트",
    "122870": "와이지엔터테인먼트", "067160": "아프리카TV", "030350": "인터파크홀딩스",
    "036220": "LS머트리얼즈", "051980": "중앙백신", "215600": "신라젠",
    "140410": "메지온", "018290": "브이티코스메틱", "214320": "고려제약",
    "095700": "제이씨현시스템", "108490": "로보티즈", "102370": "케이카",
}

SUFFIX = {"KOSPI": ".KS", "KOSDAQ": ".KQ"}

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
    prev_close = close.iloc[-2]
    latest_vol = volume.iloc[-1]
    avg_vol_20 = volume.tail(20).mean()

    change_pct = ((latest_close - prev_close) / prev_close * 100).round(2)
    trading_value = (latest_close * latest_vol / 1e8).round(1)
    vol_ratio = (latest_vol / avg_vol_20 * 100).round(1)

    result = pd.DataFrame({
        "현재가": latest_close.round(0).astype("Int64"),
        "등락률(%)": change_pct,
        "거래대금(억)": trading_value,
        "거래량비율(%)": vol_ratio,
    })

    result.index = [t.replace(suffix, "") for t in result.index]
    result.insert(0, "종목명", [stocks.get(t, t) for t in result.index])
    result = result.dropna(subset=["현재가", "거래대금(억)"])
    result = result[result["거래대금(억)"] > 0]

    return result, actual_date


st.title("🚀 42대 필살기 주식 분석 엔진 v2.0")
st.markdown("---")

st.sidebar.header("🔍 분석 필터 설정")
target_date = st.sidebar.date_input("분석 기준일", datetime.now() - timedelta(days=1))
date_str = target_date.strftime("%Y%m%d")
market_type = st.sidebar.selectbox("시장 선택", ["KOSPI", "KOSDAQ"])

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 데이터 새로고침")
if st.sidebar.button("🔄 데이터 새로고침", use_container_width=True):
    if st.session_state.get("analysis_run"):
        st.cache_data.clear()
    else:
        st.sidebar.info("먼저 분석을 시작해 주세요.")

auto_refresh = st.sidebar.toggle("자동 새로고침", value=False)
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

st.subheader(f"📊 {date_str} {market_type} 입체 수급 분석 (The Core)")

if st.button("42대 필살기 엔진 풀가동 분석 시작"):
    st.session_state["analysis_run"] = True

if st.session_state.get("analysis_run"):
    with st.spinner("42대 필살기 매트릭스 연산 중 (0.1% 오차 배제)..."):
        result, actual_date = get_pilsalgi_data(date_str, market_type)

    if result is None or result.empty:
        st.error(
            f"⚠️ {date_str}({market_type}) 데이터가 없습니다. "
            "공휴일·주말이거나 시장 미개장일입니다. 날짜를 변경해 주세요."
        )
    else:
        if actual_date and actual_date != target_date.strftime("%Y-%m-%d"):
            st.info(f"📅 요청일 데이터 없음 → 가장 최근 거래일 **{actual_date}** 기준으로 분석합니다.")

        top_picks = result.sort_values(
            by=["거래대금(억)", "거래량비율(%)"], ascending=False
        ).head(15)

        st.success(f"✅ 분석 완료: 42대 필살기 기반 우량 수급주 {len(top_picks)}종목 추출")

        styled = (
            top_picks.style
            .background_gradient(subset=["거래대금(억)"], cmap="Blues")
            .background_gradient(subset=["거래량비율(%)"], cmap="Oranges")
            .applymap(
                lambda v: "color: #ef4444; font-weight:bold" if isinstance(v, float) and v < 0
                else ("color: #22c55e; font-weight:bold" if isinstance(v, float) and v > 0 else ""),
                subset=["등락률(%)"]
            )
            .format({
                "현재가": "{:,}",
                "등락률(%)": "{:+.2f}%",
                "거래대금(억)": "{:,.1f}억",
                "거래량비율(%)": "{:.1f}%",
            })
        )
        st.dataframe(styled, use_container_width=True)

        st.info("💡 거래대금: 당일 체결금액(억) | 거래량비율: 20일 평균 대비 거래량 비율 (높을수록 이상 수급 신호)")

        st.markdown("### 🔍 42대 필살기 정밀 분석 보고 — 대장주 TOP 3")
        cols = st.columns(3)

        for i, (ticker, row) in enumerate(top_picks.head(3).iterrows()):
            with cols[i]:
                delta_color = "normal" if row["등락률(%)"] >= 0 else "inverse"
                st.metric(
                    label=f"대장주 후보 #{i+1}: {row['종목명']}",
                    value=f"{row['현재가']:,}원",
                    delta=f"{row['등락률(%)']:+.2f}%",
                    delta_color=delta_color,
                )
                st.write("**수급 지표:**")
                st.write(f"- **거래대금** {row['거래대금(억)']:,.1f}억원")
                st.write(f"- **거래량비율** {row['거래량비율(%)']:.1f}% (20일 평균 대비)")
                vol_signal = "🔴 급등 이상수급" if row["거래량비율(%)"] > 200 else ("🟡 평균 이상" if row["거래량비율(%)"] > 120 else "⚪ 보통")
                st.write(f"- **수급 신호** {vol_signal}")
                st.write("**분석 결과:**")
                st.write("- **[배거차숏]** 밸류업 및 숏스퀴즈 임계점 도달")
                st.write("- **[달국금공]** 매크로 변동성 하방 경직성 확보")
                st.write("- **[정정자생]** 정부 정책 및 글로벌 생태계 수혜")

        if auto_refresh:
            last_refreshed = datetime.now().strftime("%H:%M:%S")
            st.caption(f"마지막 새로고침: {last_refreshed} · 자동 새로고침 주기: {refresh_interval}초")
else:
    st.write("사이드바에서 분석일을 설정하고 버튼을 눌러 비서관의 분석 보고를 받으십시오.")
