import sys
import shutil

# 1. 안전제일: 무조건 백업부터 생성
shutil.copy2('/home/ubuntu/main.py', '/home/ubuntu/main_backup.py')
print(">> [1/3] Backup Success: main_backup.py created.")

with open('/home/ubuntu/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 2. 기존 좁은 V3 블록 제거
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if "SUMBI V3 PRESTIGE ENGINE" in line:
        start_idx = i - 1
    if "st.error(f\"V3 System Error:" in line and start_idx != -1:
        end_idx = i + 1
        break

if start_idx != -1 and end_idx != -1:
    del lines[start_idx:end_idx]

# 3. 고급 영/한 병기 + 대형 폰트 V3 UI 생성 (인코딩 안전 유니코드 사용)
v3_upgraded = """
# ================================================================
# SUMBI V3 PRESTIGE ENGINE & UI (BILINGUAL & LARGE FONT)
# ================================================================
try:
    from v3_scorer import calc_sumbi_v3
    def get_short_data_mock(): return {'short_ratio': 2.5, 'loan_change': -5.0}
    def get_sector_data_mock(): return {'relative_strength': 0.03, 'foreign_flow': 1500}
    def get_broker_data_mock(): return {'foreign_buy': 2, 'top_buy_consensus': 3}
    
    v3_result = calc_sumbi_v3(investor=investor, macro=macro, df_chart=df_chart, info=info, news_list=news_list, short_data=get_short_data_mock(), sector_data=get_sector_data_mock(), broker_data=get_broker_data_mock())
    v3_tot, v3_grd, v3_lbl, v3_brk = v3_result["total"], v3_result["grade"], v3_result["grade_label"], v3_result["breakdown"]
    
    g_colors = {"S+": "#00FF94", "S": "#34C759", "A+": "#FFD60A", "A": "#FFD60A", "B": "#FF9500", "C": "#FF6B35", "D": "#FF3B3B"}
    g_icons = {"S+": "&#128293;", "S": "&#9989;", "A+": "&#11088;", "A": "&#11088;", "B": "&#128202;", "C": "&#9888;&#65039;", "D": "&#128680;"}
    vc, vi = g_colors.get(v3_grd, "#FFD60A"), g_icons.get(v3_grd, "&#128202;")
    
    st.markdown("<div class='panel' style='margin-bottom:24px;'><div class='sec-label' style='font-size:18px;'>| SUMBI SCORE V3 <span class='sec-sub' style='font-size:14px;'>/ 8 Items 100pts</span></div>", unsafe_allow_html=True)
    st.markdown(f'<div style="background:rgba(0,0,0,0.4);border:2px solid {vc}60;border-radius:20px;padding:28px;margin:12px 0;display:flex;align-items:center;gap:20px;"><div style="font-size:55px;">{vi}</div><div style="flex:1;"><div style="font-family:JetBrains Mono,monospace;font-size:13px;color:#52525b;letter-spacing:.1em;">SUMBI PRESTIGE SCORE V3 / \uc228\ube44 \uc885\ud569 \ud22c\uc790 \uc810\uc218</div><div style="display:flex;align-items:baseline;gap:12px;margin:8px 0;"><span style="font-family:Cormorant Garamond,serif;font-size:60px;color:{vc};font-weight:700;line-height:1;">{v3_tot}</span><span style="font-size:22px;color:#52525b;">/ 100</span><span style="background:{vc}20;border:1px solid {vc}60;border-radius:8px;padding:6px 14px;font-family:JetBrains Mono,monospace;font-size:18px;color:{vc};font-weight:700;">{v3_grd}</span></div><div style="font-size:16px;color:#a0a0a0;letter-spacing:.05em;font-weight:600;">{v3_lbl}</div></div></div>', unsafe_allow_html=True)
    
    v3_labels = [("flow", "&#128176; Money Flow | \uba54\uc774\uc800 \uc218\uae09", 25), ("chart", "&#128200; Chart Tech | \ucc28\ud2b8\u00b7\uae30\uc220\uc801", 25), ("fundamental", "&#127970; Fundamental | \uae30\uc5c5 \ud380\ub354\uba58\ud138", 13), ("news", "&#128240; News Momentum | \ub274\uc2a4 \ubaa8\uba58\ud140", 10), ("short", "&#128616; Short Signal | \uacf5\ub9e4\ub3c4 \uc2e0\ud638", 8), ("macro", "&#127757; Macro Env | \ub9e4\ud06c\ub85c \ud658\uacbd", 7), ("sector", "&#127912; Sector Theme | \uc139\ud130\u00b7\ud14c\ub9c8", 7), ("broker", "&#9889; Broker Flow | \uac70\ub798\uc6d0 \ubd84\uc11d", 5)]
    r_html = []
    for key, name, max_s in v3_labels:
        val, mx, _ = v3_brk.get(key, (0, max_s, {}))
        pct = int(val/mx*100) if mx>0 else 0
        bar_c = "#34C759" if pct >= 70 else "#FFD60A" if pct >= 40 else "#FF3B3B"
        r_html.append(f'<div style="background:rgba(255,255,255,0.03);border:1px solid #2a2a2a;border-radius:12px;padding:16px;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;"><span style="font-size:15px;color:#e0e0e0;font-weight:600;">{name}</span><span style="font-family:JetBrains Mono,monospace;font-size:18px;color:{bar_c};font-weight:700;">{val}<span style="color:#52525b;font-size:14px;">/{mx}</span></span></div><div style="background:#1a1a1a;border-radius:6px;height:10px;"><div style="background:{bar_c};width:{pct}%;height:10px;border-radius:6px;"></div></div></div>')
    st.markdown(f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:12px 0;'>{''.join(r_html)}</div></div>", unsafe_allow_html=True)
except Exception as e:
    st.error(f"V3 System Error: {e}")
"""

# 찾기: g_col1, g_col2 = st.columns
inject_idx = -1
for i, line in enumerate(lines):
    if "g_col1, g_col2 = st.columns" in line:
        inject_idx = i
        break

lines.insert(inject_idx, v3_upgraded)

with open('/home/ubuntu/main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print(">> [2/3] UI Code Upgraded (Bilingual, Larger Fonts).")
