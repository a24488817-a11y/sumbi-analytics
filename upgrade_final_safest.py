import os, re
filepath = os.path.expanduser("~/main.py")
with open(filepath, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Clean previous UI
code = re.sub(r'# --- (PREMIUM|PREMIER|QUANTUM) UI INJECTION.*?# -----------------*\n', '', code, flags=re.DOTALL)

# 2. Quantum UI String
quantum_ui = """
# --- QUANTUM UI INJECTION ---
def apply_quantum_ui():
    import streamlit as st
    import streamlit.components.v1 as components
    
    st.markdown('''
    <style>
    .stApp { background-color: #050810; color: #F8FAFC; }
    
    .q-title {
        text-align: center;
        font-size: 3.8rem;
        font-weight: 900;
        background: linear-gradient(135deg, #FFDF73 0%, #D4AF37 50%, #996515 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
        text-shadow: 0px 4px 20px rgba(212,175,55,0.5);
        letter-spacing: 3px;
    }
    
    .q-sub {
        text-align: center;
        color: #94A3B8;
        font-size: 1.1rem;
        letter-spacing: 5px;
        margin-bottom: 30px;
    }
    
    div[data-testid="metric-container"] {
        background-color: #0F1423;
        border: 1px solid #1E293B;
        border-left: 4px solid #D4AF37;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.6);
        transition: all 0.3s;
    }
    div[data-testid="metric-container"]:hover {
        border-color: #D4AF37;
        box-shadow: 0 4px 20px rgba(212,175,55,0.3);
        transform: translateY(-2px);
    }
    
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #1E3A8A, #2563EB);
        color: white;
        font-weight: 800;
        border: none;
        border-radius: 6px;
        height: 60px;
        font-size: 1.3rem;
        letter-spacing: 2px;
        box-shadow: 0 4px 15px rgba(37,99,235,0.4);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #1E3A8A, #1D4ED8);
        border: 1px solid #D4AF37;
    }
    </style>
    
    <div class="q-title">SUMBI QUANTUM</div>
    <div class="q-sub">INSTITUTIONAL GRADE TERMINAL | KOR_SUB</div>
    <hr style="border-color:#1E293B; margin-top:10px;">
    ''', unsafe_allow_html=True)

    # 3. Transparent AI Sensor for Colors
    components.html('''
    <script>
    function applyColors() {
        const elements = window.parent.document.querySelectorAll('[data-testid="stMetricValue"]');
        elements.forEach(el => {
            const text = el.innerText.replace(/,/g, '').replace(/%/g, '');
            const num = parseFloat(text);
            if (!isNaN(num)) {
                if (num > 0) { 
                    el.style.color = '#EF4444'; 
                } else if (num < 0) { 
                    el.style.color = '#3B82F6'; 
                }
            }
        });
    }
    setInterval(applyColors, 500); 
    </script>
    ''', height=0)

apply_quantum_ui()
# ----------------------------
"""

# Safe Korean insertion
kor_sub_raw = "42\\ub300 \\uc8fc\\uc2dd \\ud544\\uc0b4\\uae30 | \\uc815\\ubc00 \\ud0c0\\uaca9 \\uc2dc\\uc2a4\\ud15c"
kor_sub = kor_sub_raw.encode('ascii').decode('unicode_escape')
quantum_ui = quantum_ui.replace("KOR_SUB", kor_sub)

# Hide old titles
lines = code.split('\n')
for i, line in enumerate(lines):
    if line.strip().startswith('st.title') or line.strip().startswith('st.header'):
        if not line.strip().startswith('#'):
            lines[i] = '# ' + line
code = '\n'.join(lines)

# Inject
if "apply_quantum_ui()" not in code:
    insert_idx = code.find('def get_macro()')
    if insert_idx != -1:
        code = code[:insert_idx] + quantum_ui + "\n" + code[insert_idx:]
    else:
        code = quantum_ui + "\n" + code

with open(filepath, "w", encoding="utf-8") as f:
    f.write(code)

print("--- SUMBI QUANTUM TERMINAL UPGRADE COMPLETE ---")
