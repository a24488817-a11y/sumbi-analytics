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




APP_KEY = "PSlNkvE41gjhOZKi2kOvfLjN8T1kaBd63kw4"
APP_SECRET = "CktcLOq5xiMU4Ap7fV81aGU9glF871ktd0mY78hyehFxSFdWLcNPA1T9qbkTgctFXGeUVg5o9iQ/O/HIrrEM+z6nNYAgnWiNWinSl0PKHP9JrxhrRc82gx6UPZBoqrfEzIeKMmcwalzzwS3Rpj2hcxov7UTyoUcm0FoQW3SRlSFO0buByt4="
URL_BASE = "https://openapi.koreainvestment.com:9443"

st.set_page_config(layout="centered", page_title="Sumbi Analytics v4.6")

# ASCII Safe Strings
txt_title = "\uc228\ube44\uc560\ub110\ub9ac\uc2a4\ud2b8"
txt_us10 = "\ubbf8 \uad6d\ucc44 10\ub144\ubb3c \uae08\ub9ac"
txt_fx = "\uc6d0/\ub2ec\ub7ec \ud658\uc728"
txt_dxy = "\ub2ec\ub7ec \uc778\ub371\uc2a4"
txt_wti = "WTI \ubbf8\uad6d \uc6d0\uc720\uac00"
txt_terminal = "42\ub300 \ud544\uc0b4\uae30 \uc2e4\uc2dc\uac04 \uc218\uae09 \ud130\ubbf8\ub110"
txt_input = "\uc885\ubaa9\uba85/\ucf54\ub4dc \uc785\ub825:"
txt_mapping = "\uc2e4\uc2dc\uac04 \uba54\uc774\uc800 \uc218\uae09 \ub9e4\ud551"
txt_gi = "\uae30\uad00 \uc21c\ub9e4\uc218: "
txt_yeon = "\uc5f0\uae30\uae08 \ub300\ub7c9\ub9e4\uc9d1: "
txt_oe = "\uc678\uad6d\uc778 \uc218\uae09: "
txt_pro = "\ud504\ub85c\uadf8\ub7a8 \ub204\uc801: "
txt_gae = "\uac1c\uc778 \ud3ec\uc9c0\uc158: "
txt_rate = "\uc678\uc728 \ubcf4\uc720\uc728: "
txt_news = "\uad6d\uae00 \uc2e4\uc2dc\uac04 RSS \uc815\ubcf4 \ub808\uc774\ub354"

ticker_map = {
    "\ud55c\ud654\uc624\uc150": "042660",
    "\ud55c\ud654\uc5d0\uc5b4\ub85c\uc2a4\ud398\uc774\uc2a4": "012450",
    "HD\ud55c\uad6d\uc870\uc120\ud574\uc591": "009540",
    "LIG\ub125\uc2a4\uc6d0": "079550",
    "HPSP": "403040",
    "HD\ud604\ub300\uc91d\uacf5\uc5c5": "329180",
    "\ud604\ub300\ub85c\ud15c": "064350",
    "\ud55c\ud654\uc2dc\uc2a4\ud15c": "272210",
    "\ud48d\uc0b0": "005810"
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
            c1.metric('\uae30\uad00 (\uc8fc)', f'{orgn:,}')
            c2.metric('\uc678\uad6d\uc778 (\uc8fc)', f'{frgn:,}')
            c3.metric('\uac1c\uc778 (\uc8fc)', f'{prsn:,}')
            st.markdown('---')
            st.markdown('### \ucd5c\uc2e0 \ub274\uc2a4')
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
                st.write('\ub274\uc2a4\ub97c \ubd88\ub7ec\uc62c \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.')
            st.markdown('---')
            st.markdown('### \ucc28\ud2b8 \ubd84\uc11d (5\uc77c/20\uc77c\uc120)')
            try:
                import datetime
                import plotly.graph_objects as go
                start_date = (datetime.datetime.now() - datetime.timedelta(days=120)).strftime('%Y-%m-%d')
                df_chart = fdr.DataReader(ticker, start_date)
                df_chart['MA5'] = df_chart['Close'].rolling(window=5).mean()
                df_chart['MA20'] = df_chart['Close'].rolling(window=20).mean()
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name='\uc8fc\uac00'))
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA5'], line=dict(color='orange', width=1.5), name='5\uc77c\uc120'))
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA20'], line=dict(color='blue', width=1.5), name='20\uc77c\uc120'))
                fig.update_layout(template='plotly_dark', margin=dict(l=0, r=0, t=30, b=0), height=400, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.write('\ucc28\ud2b8\ub97c \ubd88\ub7ec\uc62c \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.')
            st.markdown('---')
            st.markdown('### \uc228\ube44 AI \ub525 \uc2a4\uce94 \uc810\uc218')
            score_supply = 0
            if 'orgn' in locals() and orgn > 0: score_supply += 15
            if 'frgn' in locals() and frgn > 0: score_supply += 15
            score_chart = 0
            try:
                if df_chart['Close'].iloc[-1] > df_chart['MA5'].iloc[-1]: score_chart += 10
                if df_chart['Close'].iloc[-1] > df_chart['MA20'].iloc[-1]: score_chart += 10
            except:
                pass
            total_score = score_supply + score_chart
            col_s1, col_s2, col_s3 = st.columns(3)
            col_s1.metric('\ud604\uc7ac \uc810\uc218(50\uc810\ub9cc\uc810)', f'{total_score}\uc810')
            col_s2.metric('\uc218\uae09 \uc810\uc218', f'{score_supply}\uc810')
            col_s3.metric('\ucc28\ud2b8 \uc810\uc218', f'{score_chart}\uc810')
            st.info('\uacf5\ub9e4\ub3c4/\uc2e0\uc6a9 \ubc0f \uae30\uc5c5\uac00\uce58\ub294 API \uc5f0\ub3d9 \ub300\uae30 \uc911\uc785\ub2c8\ub2e4.')
        except Exception as e: st.error(f"API Error: {type(e).__name__}: {e}")
