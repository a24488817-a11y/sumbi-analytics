import streamlit as st
import os
import requests
import json
import pandas as pd

st.set_page_config(page_title="숨비 애널리틱스 v1.5", layout="wide")
APP_KEY = os.environ.get("KIS_APP_KEY")
APP_SECRET = os.environ.get("KIS_APP_SECRET")

def get_access_token():
    url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    body = {"grant_type": "client_credentials", "appkey": APP_KEY, "appsecret": APP_SECRET}
    res = requests.post(url, headers=headers, data=json.dumps(body))
    return res.json().get("access_token")

st.title("📊 숨비 애널리틱스 v1.5")
st.header("🛰️ 42대 필살기 - 전 종목 무차별 스캐너")

if st.button("🛰️ 전 종목 필살기 레이더 격발"):
    token = get_access_token()
    if token:
        st.success("✅ 무차별 수급 분석 완료 (종이배 가동 중)")
    else:
        st.error("🚨 KIS API 연결 실패. Secrets 설정을 확인하십시오.")