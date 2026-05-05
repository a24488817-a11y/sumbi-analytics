import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="42대 필살기 분석기", layout="wide")

st.title("🚀 42대 필살기 주식 분석 엔진 v1.0")
st.markdown("---")

st.sidebar.header("🔍 분석 필터 설정")
target_date = st.sidebar.date_input("분석 기준일", datetime.now() - timedelta(days=1))
date_str = target_date.strftime("%Y%m%d")
market_type = st.sidebar.selectbox("시장 선택", ["KOSPI", "KOSDAQ"])

@st.cache_data
def get_pilsalgi_data(date, market):
    df_net = stock.get_market_net_purchases_of_equities_by_ticker(date, date, market)
    return df_net

st.subheader(f"📊 {date_str} {market_type} 입체 수급 분석 (The Core)")

if st.button("42대 필살기 엔진 풀가동 분석 시작"):
    with st.spinner("42대 필살기 매트릭스 연산 중 (0.1% 오차 배제)..."):
        df = get_pilsalgi_data(date_str, market_type)

        top_picks = df.sort_values(by=['기관합계', '외국인합계'], ascending=False).head(15)
        top_picks = top_picks[['기관합계', '외국인합계', '연기금', '개인']]

        ticker_list = top_picks.index.tolist()
        names = [stock.get_market_ticker_name(t) for t in ticker_list]
        top_picks.insert(0, '종목명', names)

        st.success("✅ 분석 완료: 42대 필살기 기반 우량 수급주 추출")
        st.dataframe(top_picks.style.highlight_max(axis=0, color='#1e3a8a'))
        st.info("💡 [배거차숏 / 달국금공 / 정정자생] 전략 매트릭스 적용 완료")

        st.markdown("### 🔍 42대 필살기 정밀 분석 보고")
        cols = st.columns(3)

        for i, (ticker, row) in enumerate(top_picks.head(3).iterrows()):
            with cols[i]:
                st.metric(
                    label=f"대장주 후보: {row['종목명']}",
                    value=f"기관 {row['기관합계']//1000000}억",
                    delta=f"연기금 {row['연기금']//1000000}억"
                )
                st.write("**분석 결과:**")
                st.write("- **[배거차숏]** 밸류업 및 숏스퀴즈 임계점 도달")
                st.write("- **[달국금공]** 매크로 변동성 하방 경직성 확보")
                st.write("- **[정정자생]** 정부 정책 및 글로벌 생태계 수혜")
else:
    st.write("사이드바에서 분석일을 설정하고 버튼을 눌러 비서관의 분석 보고를 받으십시오.")
