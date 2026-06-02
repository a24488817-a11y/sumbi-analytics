import os, re
filepath = os.path.expanduser("~/main.py")
with open(filepath, "r", encoding="utf-8") as f: code = f.read()

# 1. 디자인 코드 완전 박멸 (q-title, metric-container 관련 모든 흔적 삭제)
code = re.sub(r'<style>.*?</style>', '', code, flags=re.DOTALL)
code = re.sub(r'<div class="q-title">.*?</div>', '', code, flags=re.DOTALL)
code = re.sub(r'<div class="q-sub">.*?</div>', '', code, flags=re.DOTALL)
code = re.sub(r'# --- QUANTUM UI INJECTION ---.*?# -----------------*\n', '', code, flags=re.DOTALL)

# 2. 아주 깨끗한 백지 상태에 딱 한 번만 디자인 주입
v6_final = """
# --- QUANTUM UI INJECTION ---
def apply_ui():
    import streamlit as st
    st.markdown('''<style>
    .stApp{background:#000; color:#fff;}
    .q-title{text-align:center; font-size:3rem; font-weight:900; background:linear-gradient(90deg,#BF953F,#FCF6BA,#B38728,#FBF5B7); -webkit-background-clip:text; -webkit-text-fill-color:transparent;}
    div[data-testid="metric-container"]{background:transparent; border-bottom:1px solid #222; padding:15px 0;}
    div[data-testid="stMetricValue"]>div{font-size:2.5rem !important;}
    </style>
    <div class="q-title">SUMBI ANALYTICS</div>''', unsafe_allow_html=True)
apply_ui()
# ----------------------------
"""
# get_macro 함수 앞에 깔끔하게 삽입
code = re.sub(r'def get_macro\(\):', v6_final + '\ndef get_macro():', code)

with open(filepath, "w", encoding="utf-8") as f: f.write(code)
