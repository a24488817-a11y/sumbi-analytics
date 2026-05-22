import os
from dotenv import load_dotenv
load_dotenv()
import FinanceDataReader as fdr
import streamlit as st
import requests
import json
import xml.etree.ElementTree as ET

import yfinance as yf

@st.cache_data(ttl=300)
def get_macro():
    symbols = {"tnx": "^TNX", "dxy": "DX-Y.NYB", "krw": "KRW=X", "wti": "CL=F"}
    result = {}
    for key, sym in symbols.items():
        try:
            data = yf.Ticker(sym).history(period="2d")
            result[key] = float(data["Close"].iloc[-1]) if not data.empty else None
        except:
            result[key] = None
    return result

@st.cache_data(ttl=3600)
def get_token():
    try:
        res = requests.post(
            f"{URL_BASE}/oauth2/tokenP",
            json={"grant_type":"client_credentials","appkey":APP_KEY,"appsecret":APP_SECRET}
        ).json()
        return res.get("access_token")
    except:
        return None




APP_KEY = os.environ.get("KIS_APP_KEY")
APP_SECRET = os.environ.get("KIS_APP_SECRET")
URL_BASE = "https://openapi.koreainvestment.com:9443"

st.set_page_config(layout="centered", page_title="Sumbi Analytics v4.6")

# ASCII Safe Strings
txt_title = "숨비애널리스트"
txt_us10 = "미 국채 10년물 금리"
txt_fx = "원/달러 환율"
txt_dxy = "달러 인덱스"
txt_wti = "WTI 미국 원유가"
txt_terminal = "42대 필살기 실시간 수급 터미널"
txt_input = "종목명/코드 입력:"
txt_mapping = "실시간 메이저 수급 매핑"
txt_gi = "기관 순매수: "
txt_yeon = "연기금 대량매집: "
txt_oe = "외국인 수급: "
txt_pro = "프로그램 누적: "
txt_gae = "개인 포지션: "
txt_rate = "외율 보유율: "
txt_news = "국글 실시간 RSS 정보 레이더"

ticker_map = {
    "한화오셐": "042660",
    "한화에어로스페이스": "012450",
    "HD한국조선해양": "009540",
    "LIG넥스원": "079550",
    "HPSP": "403040",
    "HD현대줝공업": "329180",
    "현대로템": "064350",
    "한화시스템": "272210",
    "풍산": "005810"
}

st.markdown("""<style>.stApp{background-color:#0E1117;}.gold-title{text-align:center;font-size:3.5rem;font-weight:950;background:linear-gradient(180deg,#FFF1B8 0%,#F3B02C 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}.card{background-color:#16161b;border:1px solid #F3B02C;border-radius:10px;padding:15px;text-align:center;}.card-val{font-size:1.4rem;font-weight:800;color:#FFFFFF;}</style>""", unsafe_allow_html=True)

st.markdown('<h1 class="gold-title">SUMBI ANALYTICS</h1>', unsafe_allow_html=True)
st.markdown(f'<h2 style="text-align:center; color:white;">{txt_title}</h2>', unsafe_allow_html=True)

macro = get_macro()
m1, m2, m3, m4 = st.columns(4)
tnx = f"{macro['tnx']:.2f}%" if macro['tnx'] else 'N/A'
krw = f"{macro['krw']:.1f}" if macro['krw'] else 'N/A'
dxy = f"{macro['dxy']:.2f}" if macro['dxy'] else 'N/A'
wti = f"{macro['wti']:.2f}" if macro['wti'] else 'N/A'
m1.markdown(f'<div class="card">{txt_us10}<br><div class="card-val">{tnx}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="card">{txt_fx}<br><div class="card-val">{krw}</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="card">{txt_dxy}<br><div class="card-val">{dxy}</div></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="card">{txt_wti}<br><div class="card-val">{wti}</div></div>', unsafe_allow_html=True)


@st.cache_data(ttl=86400)
def get_stock_code(name):
    if name.isdigit(): return name
    try:
        df = fdr.StockListing('KRX')
        mapping = dict(zip(df['Name'], df['Code']))
        return mapping.get(name, name)
    except:
        return name

user_input = st.text_input(txt_input, value="")
if st.button("EXECUTE DEEP SCAN"):
    ticker = get_stock_code(user_input)
    if len(ticker) == 6:
        try:
            token = get_token()
            res = requests.get(f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-investor", headers={"authorization": f"Bearer {token}", "appkey": APP_KEY, "appsecret": APP_SECRET, "tr_id": "FHKST01010900"}, params={"fid_cond_mrkt_div_code": "J", "fid_input_iscd": ticker}).json()["output"][0]
            st.markdown(f'<div class="card" style="text-align:center;">{txt_mapping}</div>', unsafe_allow_html=True)
            orgn = int(res.get('orgn_ntby_qty', '0'))
            frgn = int(res.get('frgn_ntby_qty', '0'))
            prsn = int(res.get('prsn_ntby_qty', '0'))
            c1, c2, c3 = st.columns(3)
            c1.metric('기관 (주)', f'{orgn:,}')
            c2.metric('외국인 (주)', f'{frgn:,}')
            c3.metric('개인 (주)', f'{prsn:,}')
            st.markdown('---')
            st.markdown('### 최신 뉴스')
            try:
                import requests, urllib.parse
                import xml.etree.ElementTree as ET
                q = urllib.parse.quote(user_input)
                r = requests.get(f'https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko', timeout=5)
                root = ET.fromstring(r.text)
                items = root.findall('.//item')[:5]
                for item in items:
                    title = item.find('title').text
                    link = item.find('link').text
                    st.markdown(f'- [{title}]({link})')
            except Exception as e:
                st.write('뉴스를 불러올 수 없습니다.')
            st.markdown('---')
            st.markdown('### 차트 분석 (5일/20일선)')
            try:
                import datetime
                import plotly.graph_objects as go
                start_date = (datetime.datetime.now() - datetime.timedelta(days=120)).strftime('%Y-%m-%d')
                df_chart = fdr.DataReader(ticker, start_date)
                df_chart['MA5'] = df_chart['Close'].rolling(window=5).mean()
                df_chart['MA20'] = df_chart['Close'].rolling(window=20).mean()
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name='주가'))
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA5'], line=dict(color='orange', width=1.5), name='5일선'))
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA20'], line=dict(color='blue', width=1.5), name='20일선'))
                fig.update_layout(template='plotly_dark', margin=dict(l=0, r=0, t=30, b=0), height=400, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.write('차트를 불러올 수 없습니다.')
        except Exception as e: st.error(f"API Error: {type(e).__name__}: {e}")
