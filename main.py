import streamlit as st
import os
import requests
import json
import pandas as pd

# 1. 앱 기본 설정 (숨비 애널리틱스 v1.5)
st.set_page_config(page_title="숨비 애널리틱스 v1.5", layout="wide")

st.title("📊 숨비 애널리틱스 v1.5")
st.subheader("🛰️ 42대 주식 필살기 - 전 종목 무차별 스캐너")

# 2. 무결점 KIS API 시크릿 키 로딩 함수 (따옴표 충돌 및 띄어쓰기 완벽 차단)
def get_kis_secret(key_name):
    if key_name in st.secrets:
        return str(st.secrets[key_name]).strip('"\' ')
    elif key_name in os.environ:
        return str(os.environ[key_name]).strip('"\' ')
    return None

# API 환경변수 할당
APP_KEY = get_kis_secret("KIS_APP_KEY")
APP_SECRET = get_kis_secret("KIS_APP_SECRET")
ACC_NO = get_kis_secret("KIS_ACC_NO")

# 3. KIS API 접근 토큰(Access Token) 발급 함수
def get_access_token(app_key, app_secret):
    # 실전투자용 도메인 (모의투자일 경우 도메인이 다름)
    url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret
    }
    try:
        res = requests.post(url, headers=headers, data=json.dumps(body))
        if res.status_code == 200:
            return res.json().get("access_token")
        else:
            return None
    except Exception as e:
        return None

# 4. 생사결단 검증 및 스캐너 가동 로직
if st.button("🛰️ 전 종목 필살기 레이더 격발"):
    if not APP_KEY or not APP_SECRET or not ACC_NO:
        st.error("🚨 KIS API 연결 실패. Secrets 설정(APP_KEY, APP_SECRET, ACC_NO)이 누락되었습니다.")
        st.stop()
    
    with st.spinner("한국투자증권 서버와 보안 통신을 시도 중입니다..."):
        token = get_access_token(APP_KEY, APP_SECRET)
        
        if token:
            st.success("✅ KIS API 토큰 발급 성공! 42대 주식 필살기 레이더 통신망이 열렸습니다.")
            st.info("데이터 수급기관(기관, 외국인, 프로그램, 연기금) 스캔 준비 완료.")
        else:
            st.error("🚨 토큰 발급 실패. 앱 키/시크릿 키가 잘못되었거나, KIS 서버 점검 중일 수 있습니다.")

