import os

filepath = os.path.expanduser("~/main.py")
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

with open(os.path.expanduser("~/main_backup_ui.py"), "w", encoding="utf-8") as f:
    f.writelines(lines)

premium_ui_code = """
# --- PREMIUM UI INJECTION ---
def apply_premium_ui():
    import streamlit as st
    st.markdown('''
    <style>
    .stApp { background-color: #0B0F19; color: #F8FAFC; font-family: 'Helvetica Neue', sans-serif; }
    .grand-title { 
        background: linear-gradient(90deg, #D4AF37, #FDE047, #D4AF37); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        font-size: 3.2rem; 
        font-weight: 900; 
        text-align: center; 
        letter-spacing: 2px;
        margin-bottom: 5px; 
        text-shadow: 0px 4px 20px rgba(212,175,55,0.3); 
    }
    .sub-title { 
        text-align: center; 
        color: #94A3B8; 
        font-size: 1.1rem; 
        letter-spacing: 5px; 
        font-weight: 600; 
        margin-bottom: 35px; 
    }
    div[data-testid="metric-container"] { 
        background-color: #151C2C; 
        border: 1px solid #1E293B; 
        border-radius: 12px; 
        padding: 20px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.5); 
        transition: all 0.3s ease; 
    }
    div[data-testid="metric-container"]:hover { 
        border-color: #D4AF37; 
        box-shadow: 0 0 20px rgba(212,175,55,0.2); 
        transform: translateY(-3px); 
    }
    .stButton>button { 
        width: 100%; 
        background: linear-gradient(90deg, #1E3A8A, #2563EB); 
        color: white; 
        font-weight: bold; 
        font-size: 1.3rem; 
        border-radius: 8px; 
        border: none; 
        padding: 15px; 
        transition: all 0.3s; 
        letter-spacing: 2px;
    }
    .stButton>button:hover { 
        background: linear-gradient(90deg, #2563EB, #3B82F6); 
        box-shadow: 0 0 20px rgba(59,130,246,0.6); 
    }
    </style>
    
    <div class="grand-title">SUMBI ANALYTICS : QUANTUM</div>
    <div class="sub-title">INSTITUTIONAL GRADE TERMINAL | KOR_TEXT_PLACEHOLDER</div>
    ''', unsafe_allow_html=True)

apply_premium_ui()
# ----------------------------
"""

# Inject Korean text safely using Python's native unicode decoding
kor_text = "42\ub300 \uc8fc\uc2dd \ud544\uc0b4\uae30 | \uc815\ubc00 \ud0c0\uaca9 \uc2dc\uc2a4\ud15c"
premium_ui_code = premium_ui_code.replace("KOR_TEXT_PLACEHOLDER", kor_text)

already_injected = False
for i, line in enumerate(lines):
    if "PREMIUM UI INJECTION" in line:
        already_injected = True
    if "st.title(" in line or "st.header(" in line:
        lines[i] = "# " + line

if not already_injected:
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            insert_idx = i + 1
    lines.insert(insert_idx, premium_ui_code + "\n")

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("--- PREMIUM UI UPGRADE SUCCESS ---")
else:
    print("--- UI ALREADY UPGRADED ---")
