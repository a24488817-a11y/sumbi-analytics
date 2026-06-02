import sys

with open('/home/ubuntu/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1단계: 기존에 잘못 들어간 '죽은 코드' 덩어리 도려내기
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

# 2단계: 렌더링 될 정확한 위치 찾기
inject_idx = -1
for i, line in enumerate(lines):
    if "g_col1, g_col2 = st.columns" in line:
        inject_idx = i
        break

# 3단계: 들여쓰기 0칸(Flush Left)으로 메인 흐름에 V3 강제 주입
v3_flush_left = """
# ================================================================
# SUMBI V3 PRESTIGE ENGINE & UI (FULL WIDTH)
# ================================================================
try:
    from v3_scorer import calc_sumbi_v3
    def get_short_data_mock(): return {'short_ratio': 2.5, 'loan_change': -5.0}
    def get_sector_data_mock(): return {'relative_strength': 0.03, 'foreign_flow': 1500}
    def get_broker_data_mock(): return {'foreign_buy': 2, 'top_buy_consensus': 3}
    
    v3_result = calc_sumbi_v3(investor=investor, macro=macro, df_chart=df_chart, info=info, news_list=news_list, short_data=get_short_data_mock(), sector_data=get_sector_data_mock(), broker_data=get_broker_data_mock())
    v3_tot, v3_grd, v3_lbl, v3_brk = v3_result["total"], v3_result["grade"], v3_result["grade_label"], v3_result["breakdown"]
    
    g_colors = {"S+": "#00FF94", "S": "#34C759", "A+": "#FFD60A", "A": "#FFD60A", "B": "#FF9500", "C": "#FF6B35", "D": "#FF3B3B"}
    g_icons = {"S+": "https://img.icons8.com/emoji/96/fire.png", "S": "https://img.icons8.com/emoji/96/check-mark-button.png", "A+": "https://img.icons8.com/emoji/96/star.png", "A": "https://img.icons8.com/emoji/96/star.png", "B": "https://img.icons8.com/emoji/96/bar-chart.png", "C": "https://img.icons8.com/emoji/96/warning.png", "D": "https://img.icons8.com/emoji/96/sos-button.png"}
    vc, vi = g_colors.get(v3_grd, "#FFD60A"), g_icons.get(v3_grd, "https://img.icons8.com/emoji/96/bar-chart.png")
    
    st.markdown("<div class='panel' style='margin-bottom:24px;'><div class='sec-label'>| SUMBI SCORE V3 <span class='sec-sub'>/ 8 Items 100pts</span></div>", unsafe_allow_html=True)
    st.markdown(f'<div style="background:rgba(0,0,0,0.4);border:2px solid {vc}60;border-radius:20px;padding:24px;margin:12px 0;display:flex;align-items:center;gap:20px;"><img src="{vi}" style="width:64px;height:64px;flex-shrink:0;"/><div style="flex:1;"><div style="font-family:JetBrains Mono,monospace;font-size:10px;color:#52525b;letter-spacing:.2em;">SUMBI PRESTIGE SCORE V3</div><div style="display:flex;align-items:baseline;gap:12px;margin:6px 0;"><span style="font-family:Cormorant Garamond,serif;font-size:52px;color:{vc};font-weight:700;line-height:1;">{v3_tot}</span><span style="font-size:18px;color:#52525b;">/100</span><span style="background:{vc}20;border:1px solid {vc}60;border-radius:8px;padding:4px 12px;font-family:JetBrains Mono,monospace;font-size:14px;color:{vc};font-weight:700;">{v3_grd}</span></div><div style="font-size:14px;color:#a0a0a0;letter-spacing:.05em;">{v3_lbl}</div></div></div>', unsafe_allow_html=True)
    
    v3_labels = [("flow", "&#128176; Money Flow", 25), ("chart", "&#128200; Chart Tech", 25), ("fundamental", "&#127970; Fundamental", 13), ("news", "&#128240; News Momentum", 10), ("short", "&#128616; Short Signal", 8), ("macro", "&#127757; Macro Env", 7), ("sector", "&#127912; Sector Theme", 7), ("broker", "&#9889; Broker Flow", 5)]
    r_html = []
    for key, name, max_s in v3_labels:
        val, mx, _ = v3_brk.get(key, (0, max_s, {}))
        pct = int(val/mx*100) if mx>0 else 0
        bar_c = "#34C759" if pct >= 70 else "#FFD60A" if pct >= 40 else "#FF3B3B"
        r_html.append(f'<div style="background:rgba(255,255,255,0.03);border:1px solid #2a2a2a;border-radius:12px;padding:12px 16px;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;"><span style="font-size:13px;color:#e0e0e0;">{name}</span><span style="font-family:JetBrains Mono,monospace;font-size:14px;color:{bar_c};font-weight:700;">{val}<span style="color:#52525b;font-size:10px;">/{mx}</span></span></div><div style="background:#1a1a1a;border-radius:4px;height:6px;"><div style="background:{bar_c};width:{pct}%;height:6px;border-radius:4px;"></div></div></div>')
    st.markdown(f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0;'>{''.join(r_html)}</div></div>", unsafe_allow_html=True)
except Exception as e:
    st.error(f"V3 System Error: {e}")

"""
lines.insert(inject_idx, v3_flush_left)

with open('/home/ubuntu/main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
