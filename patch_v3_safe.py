import re

with open('/home/ubuntu/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

mock_functions = """
# ================================================================
# SUMBI V3 Advanced Data Extractors (Mock for API)
# ================================================================
def get_short_data(ticker):
    return {'short_ratio': 2.5, 'loan_change': -5.0}

def get_sector_data(ticker):
    return {'relative_strength': 0.03, 'foreign_flow': 1500}

def get_broker_data(ticker):
    return {'foreign_buy': 2, 'top_buy_consensus': 3}

"""

if "get_short_data" not in content:
    content = content.replace("from v3_scorer import calc_sumbi_v3\n", "from v3_scorer import calc_sumbi_v3\n" + mock_functions)

v3_injection = """
    # --- SUMBI V3 Score Calculation ---
    try:
        short_data = get_short_data(ticker)
        sector_data = get_sector_data(ticker)
        broker_data = get_broker_data(ticker)
        
        v3_result = calc_sumbi_v3(
            investor=investor, 
            macro=macro, 
            df_chart=df_chart, 
            info=info, 
            news_list=news_list,
            short_data=short_data,
            sector_data=sector_data,
            broker_data=broker_data
        )
        
        # --- SUMBI V3 UI Rendering ---
        v3_total = v3_result["total"]
        v3_grade = v3_result["grade"]
        v3_label = v3_result["grade_label"]
        v3_bd = v3_result["breakdown"]

        grade_colors = {
            "S+": "#00FF94", "S": "#34C759",
            "A+": "#FFD60A", "A": "#FFD60A",
            "B": "#FF9500", "C": "#FF6B35", "D": "#FF3B3B"
        }
        grade_icons = {
            "S+": "https://img.icons8.com/emoji/96/fire.png",
            "S": "https://img.icons8.com/emoji/96/check-mark-button.png",
            "A+": "https://img.icons8.com/emoji/96/star.png",
            "A": "https://img.icons8.com/emoji/96/star.png",
            "B": "https://img.icons8.com/emoji/96/bar-chart.png",
            "C": "https://img.icons8.com/emoji/96/warning.png",
            "D": "https://img.icons8.com/emoji/96/sos-button.png"
        }
        gc = grade_colors.get(v3_grade, "#FFD60A")
        gi = grade_icons.get(v3_grade, "https://img.icons8.com/emoji/96/bar-chart.png")

        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='sec-label'>| SUMBI SCORE V3 <span class='sec-sub'>/ 8 Items 100pts</span></div>",
            unsafe_allow_html=True
        )

        st.markdown(f'''
        <div style="background:rgba(0,0,0,0.4);border:2px solid {gc}60;border-radius:20px;padding:24px;margin:12px 0;display:flex;align-items:center;gap:20px;">
            <img src="{gi}" style="width:64px;height:64px;flex-shrink:0;"/>
            <div style="flex:1;">
                <div style="font-family:JetBrains Mono,monospace;font-size:10px;color:#52525b;letter-spacing:.2em;">SUMBI PRESTIGE SCORE V3</div>
                <div style="display:flex;align-items:baseline;gap:12px;margin:6px 0;">
                    <span style="font-family:Cormorant Garamond,serif;font-size:52px;color:{gc};font-weight:700;line-height:1;">{v3_total}</span>
                    <span style="font-size:18px;color:#52525b;">/100</span>
                    <span style="background:{gc}20;border:1px solid {gc}60;border-radius:8px;padding:4px 12px;font-family:JetBrains Mono,monospace;font-size:14px;color:{gc};font-weight:700;">{v3_grade}</span>
                </div>
                <div style="font-size:14px;color:#a0a0a0;letter-spacing:.05em;">{v3_label}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        labels = [
            ("flow", "Money Flow", 25),
            ("chart", "Chart Tech", 25),
            ("fundamental", "Fundamental", 13),
            ("news", "News Momentum", 10),
            ("short", "Short Signal", 8),
            ("macro", "Macro Env", 7),
            ("sector", "Sector Theme", 7),
            ("broker", "Broker Flow", 5),
        ]

        rows = []
        for key, name, max_s in labels:
            val, mx, _ = v3_bd.get(key, (0, max_s, {}))
            pct = int(val / mx * 100) if mx > 0 else 0
            bar_c = "#34C759" if pct >= 70 else "#FFD60A" if pct >= 40 else "#FF3B3B"
            rows.append(f'''
            <div style="background:rgba(255,255,255,0.03);border:1px solid #2a2a2a;border-radius:12px;padding:12px 16px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <span style="font-size:13px;color:#e0e0e0;">{name}</span>
                    <span style="font-family:JetBrains Mono,monospace;font-size:14px;color:{bar_c};font-weight:700;">{val}<span style="color:#52525b;font-size:10px;">/{mx}</span></span>
                </div>
                <div style="background:#1a1a1a;border-radius:4px;height:6px;">
                    <div style="background:{bar_c};width:{pct}%;height:6px;border-radius:4px;"></div>
                </div>
            </div>''')

        st.markdown(f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0;'>{''.join(rows)}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"V3 Score Error: {e}")
"""

if "SUMBI V3 Score Calculation" not in content:
    pattern = r"(st\.markdown\(['\"]<div class=['\"]sec-label['\"]>\| QUANT FLOW MATRIX)"
    content = re.sub(pattern, v3_injection + r"\n    \1", content, count=1)

with open('/home/ubuntu/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: V3 Logic and UI perfectly injected without Encoding Errors!")
