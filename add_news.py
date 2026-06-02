import os, re

app_key, app_secret = "", ""
if os.path.exists("main.py"):
    with open("main.py", "r", encoding="utf-8") as f:
        for line in f:
            if "APP_KEY" in line and "=" in line:
                m = re.search(r"['\"]([A-Za-z0-9]+)['\"]", line)
                if m: app_key = m.group(1)
            if "APP_SECRET" in line and "=" in line:
                m = re.search(r"['\"]([A-Za-z0-9]+)['\"]", line)
                if m: app_secret = m.group(1)

code = f"""import streamlit as st
import requests
import json
import xml.etree.ElementTree as ET
import re

APP_KEY = "{app_key}"
APP_SECRET = "{app_secret}"
URL_BASE = "https://openapi.koreainvestment.com:9443"

# 🎯 대표님이 쟁취하신 네이버 정품 마스터 키 장착 완료!
NAVER_ID = "UlEYYbVmKljbYu4ENYwC"
NAVER_SECRET = "ZolUo5lgi9"

st.set_page_config(layout="centered", page_title="Sumbi Analytics v4")

st.markdown(\"\"\"
<style>
.stApp {{ background-color: #0E1117; }}
.gold-header {{
    text-align: center; font-size: 2.3rem; font-weight: 900;
    background: linear-gradient(to right, #BF953F, #FCF6BA, #B38728);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    padding: 10px 0;
}}
.card {{
    background-color: rgba(30, 30, 35, 0.8);
    border: 1px solid #BF953F; border-radius: 15px;
    padding: 20px; text-align: center; margin: 10px 0;
}}
.card-title {{ font-size: 0.9rem; color: #888888; font-weight: 600; }}
.card-value {{ font-size: 2rem; font-weight: 800; color: #FCF6BA; margin-top: 5px; }}
.score-box {{
    background: linear-gradient(135deg, #1e1e24 0%, #2a2a35 100%);
    border: 2px solid #BF953F; border-radius: 15px; padding: 20px;
    text-align: center; margin-top: 15px;
}}
.news-box {{
    background-color: rgba(20, 20, 25, 0.9);
    border-left: 4px solid #BF953F; padding: 15px; margin-top: 10px; border-radius: 5px;
}}
.news-title {{ color: #FCF6BA; font-size: 1.1rem; font-weight: bold; margin-bottom: 5px; }}
.news-desc {{ color: #A0AEC0; font-size: 0.9rem; }}
</style>
\"\"\", unsafe_allow_html=True)

st.markdown('<h1 class="gold-header">SUMBI ANALYTICS</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#555; font-size:0.8rem; letter-spacing:2px; margin-top:-15px;">PRESTIGE TERMINAL v4.0 (NEWS RADAR)</p>', unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_token():
    try:
        res = requests.post(f"{{URL_BASE}}/oauth2/tokenP", headers={{"content-type":"application/json"}}, data=json.dumps({{
            "grant_type": "client_credentials", "appkey": APP_KEY, "appsecret": APP_SECRET
        }}))
        return res.json().get("access_token")
    except: return None

def get_data(token, ticker):
    try:
        headers = {{"Content-Type": "application/json", "authorization": f"Bearer {{token}}", "appkey": APP_KEY, "appsecret": APP_SECRET, "tr_id": "FHKST01010900"}}
        res = requests.get(f"{{URL_BASE}}/uapi/domestic-stock/v1/quotations/inquire-investor", headers=headers, params={{"fid_cond_mrkt_div_code": "J", "fid_input_iscd": ticker}})
        return res.json().get("output", [{{}}])[0]
    except: return {{}}

def get_naver_chart(ticker):
    try:
        url = f"https://fchart.stock.naver.com/sise.nhn?symbol={{ticker}}&timeframe=day&count=20&requestType=0"
        res = requests.get(url, timeout=5)
        root = ET.fromstring(res.text)
        closes = [int(item.get('data').split('|')[4]) for item in root.findall('.//item')]
        if len(closes) >= 10: return sum(closes[-5:])/5, sum(closes[-10:])/10, closes[-1]
    except: pass
    return 0, 0, 0

def get_stock_name(ticker):
    mapping = {{"042660":"한화오션", "012450":"한화에어로스페이스", "079550":"LIG넥스원", "082740":"HPSP", "009540":"HD한국조선해양"}}
    return mapping.get(ticker, ticker)

def clean_html(text):
    return re.sub('<.*?>', '', text).replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")

def get_naver_news(ticker):
    query = get_stock_name(ticker) + " 주식"
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {{"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET}}
    try:
        res = requests.get(url, headers=headers, params={{"query": query, "display": 3, "sort": "sim"}})
        return res.json().get("items", [])
    except: return []

ticker = st.text_input("ENTER TARGET CODE (6-DIGIT)", value="042660")
if st.button("⚡ EXECUTE DEEP SCAN"):
    token = get_token()
    if token:
        data = get_data(token, ticker)
        ma5, ma10, current = get_naver_chart(ticker)
        
        orgn = int(data.get("orgn_ntby_qty", 0))
        frgn = int(data.get("frgn_ntby_qty", 0))
        prsn = int(data.get("prsn_ntby_qty", 0))
        
        score = 0
        if orgn > 0: score += 5
        if frgn > 0: score += 5
        if orgn > 0 and frgn > 0: score += 5 
        if abs(orgn) > 50000 or abs(frgn) > 50000: score += 5
        if current > ma5 and ma5 > 0: score += 7
        if current > ma10 and ma10 > 0: score += 7
        if ma5 > ma10 and ma5 > 0: score += 6
        
        st.markdown(f'<div class="score-box"><h2 style="color:#BF953F; margin:0;">🎯 MONEY FLOW SCORE: {{score}} / 40</h2><p style="color:#888; font-size:0.85rem; margin:5px 0 0 0;">수급 삼각 편대 및 네이버 실시간 이평선 지지 계량분석 완료</p></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="margin-top:15px;"><h3 style="color:#BF953F; font-size:1.1rem; text-align:center;">TARGET REPORT : {{get_stock_name(ticker)}} ({{ticker}})</h3></div>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="card"><div class="card-title">INSTITUTION (기관)</div><div class="card-value">{{orgn:,}}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="card"><div class="card-title">FOREIGNER (외국인)</div><div class="card-value">{{frgn:,}}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="card"><div class="card-title">INDIVIDUAL (개인)</div><div class="card-value">{{prsn:,}}</div></div>', unsafe_allow_html=True)

        st.markdown(f'<h3 style="color:#BF953F; margin-top:30px; border-bottom:1px solid #BF953F; padding-bottom:5px;">📰 [미반영 호재] 실시간 뉴스 레이더</h3>', unsafe_allow_html=True)
        news_items = get_naver_news(ticker)
        if news_items:
            for item in news_items:
                title = clean_html(item.get("title", ""))
                desc = clean_html(item.get("description", ""))
                link = item.get("link", "#")
                st.markdown(f'<div class="news-box"><a href="{{link}}" target="_blank" style="text-decoration:none;"><div class="news-title">{{title}}</div><div class="news-desc">{{desc}}</div></a></div>', unsafe_allow_html=True)
        else:
            st.write("관련 뉴스를 찾을 수 없습니다.")
"""
with open("main.py", "w", encoding="utf-8") as f:
    f.write(code)
