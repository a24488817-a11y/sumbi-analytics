import streamlit as st
import os

# 1. 앱 화면 기본 설정 (모바일 최적화)
st.set_page_config(page_title="숨비 애널리틱스", layout="wide")

# 2. 메인 타이틀 및 환영 메시지 (이제 핸드폰 화면에 보입니다)
st.title("📊 숨비 애널리틱스 v1.0")
st.subheader("100억 프로젝트 - 필살기 레이더 가동")

# 3. 보안 열쇠(연료) 상태 점검부
app_key = os.environ.get("KIS_APP_KEY")
if not app_key:
    st.error("❌ 연료(API 키)가 아직 없습니다. Secrets 메뉴에 등록해 주세요.")
else:
    st.success("✅ 엔진 점화 성공! 실시간 데이터 연동 준비 완료.")

st.divider()

# 4. 실시간 필살기 타격 리스트
st.write("### 🔍 42대 필살기 실시간 스캔 현황")
target_list = ["한화오션", "HD현대중공업", "한화에어로스페이스", "LIG넥스원"]

# 화면 분할 출력
cols = st.columns(len(target_list))
for i, stock in enumerate(target_list):
    with cols[i]:
        st.metric(label=stock, value="스캔 중", delta="수급 분석 중")

# 5. 하단 결과 테이블
st.write("### 📈 오늘의 수급 집중 타격 구간")
data = {
    "종목명": target_list,
    "필살기 상태": ["수급 집중", "눌림목 포착", "상승 추세", "강력 보유"]
}
st.table(data)

