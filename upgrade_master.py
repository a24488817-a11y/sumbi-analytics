import os, re
filepath = os.path.expanduser("~/main.py")
with open(filepath, "r", encoding="utf-8") as f: code = f.read()

# 기존 UI 블록 깔끔하게 삭제
code = re.sub(r'# --- QUANTUM UI INJECTION.*?# -----------------*\n', '', code, flags=re.DOTALL)

# V6 MASTERPIECE UI - 들여쓰기 버그 완벽 제거 및 극강의 하이엔드 디자인
v6_ui = """
# --- QUANTUM UI INJECTION ---
def apply_quantum_ui():
    import streamlit as st
    import streamlit.components.v1 as components
    
    # HTML 코드를 맨 앞으로 당겨서 마크다운 '코드 블록' 오작동을 원천 차단했습니다.
    html_content = '''<style>
.stApp {background-color:#000000; color:#fff;}
.q-title {text-align:center; font-size:3.5rem; font-weight:900; background:linear-gradient(90deg,#BF953F,#FCF6BA,#B38728,#FBF5B7); -webkit-background-clip:text; -webkit-text-fill-color:transparent; letter-spacing:4px; padding-bottom:5px;}
.q-sub {text-align:center; color:#777; font-size:1rem; letter-spacing:5px; margin-bottom:40px; font-weight:300;}
div[data-testid="metric-container"] {background:transparent; border:none; border-bottom:1px solid #222; box-shadow:none; padding:15px 0; transition:0.4s;}
div[data-testid="metric-container"]:hover {border-bottom:1px solid #BF953F; transform:translateY(-2px);}
div[data-testid="metric-container"] label {color:#D4AF37 !important; font-size:1rem !important; letter-spacing:2px; font-weight:400 !important;}
div[data-testid="stMetricValue"]>div {font-size:2.6rem !important; font-weight:300 !important; font-family:-apple-system, sans-serif;}
div[data-testid="stTextInput"] input {background:#0A0A0A; border:none; border-bottom:2px solid #333; color:#D4AF37; border-radius:0; padding:15px; font-size:1.2rem; text-align:center;}
div[data-testid="stTextInput"] input:focus {border-bottom:2px solid #BF953F; box-shadow:none;}
.stButton>button {width:100%; background:transparent; border:1px solid #D4AF37; color:#D4AF37; height:65px; font-size:1.4rem; letter-spacing:5px; transition:0.3s; font-weight:300;}
.stButton>button:hover {background:#D4AF37; color:#000; font-weight:700;}
</style>
<div class="q-title">SUMBI ANALYTICS</div>
<div class="q-sub">MASTERPIECE TERMINAL | KOR_SUB</div>'''
    
    st.markdown(html_content, unsafe_allow_html=True)

    components.html('''<script>
    setInterval(()=>{
        document.querySelectorAll('[data-testid="metric-container"]').forEach(c=>{
            let v = c.querySelector('[data-testid="stMetricValue"]');
            if(v){
                let n = parseFloat(v.innerText.replace(/,/g,'').replace(/%/g,''));
                if(n<0) { v.style.color='#0A84FF'; } 
                else if(n>0) { v.style.color='#FF3B30'; } 
                else { v.style.color='#FFFFFF'; }
            }
        });
    }, 400);
    </script>''', height=0)
apply_quantum_ui()
# ----------------------------
"""

kor_sub_raw = "42\\ub300 \\uc8fc\\uc2dd \\ud544\\uc0b4\\uae30 | \\uc815\\ubc00 \\ud0c0\\uaca9 \\uc2dc\\uc2a4\\ud15c"
v6_ui = v6_ui.replace("KOR_SUB", kor_sub_raw.encode('ascii').decode('unicode_escape'))

insert_idx = code.find('def get_macro()')
if insert_idx != -1: code = code[:insert_idx] + v6_ui + "\n" + code[insert_idx:]
else: code = v6_ui + "\n" + code

# [엔진 무결점 패치] 빈 데이터(공백)가 들어오면 ValueError를 뿜고 마비되는 버그를 원천 차단
# int(변수)를 호출할 때, 변수가 비어있으면 안전하게 0으로 치환하도록 정규식으로 방어 코드를 씌웁니다.
code = re.sub(r'int\((.*?)\)', r'(int(\1) if str(\1).strip() else 0)', code)

with open(filepath, "w", encoding="utf-8") as f: f.write(code)
