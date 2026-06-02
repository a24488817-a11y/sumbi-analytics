with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = "st.markdown('<div class=\"sec-label\">| QUANT FLOW MATRIX"

v3_ui = """
if v3_result:
    v3_tot = v3_result["total"]
    v3_grd = v3_result["grade"]
    v3_lbl = v3_result["grade_label"]
    gc_map = {"S+":"#00FF94","S":"#34C759","A+":"#FFD60A","A":"#FFD60A","B":"#FF9500","C":"#FF6B35","D":"#FF3B3B"}
    gc = gc_map.get(v3_grd, "#FFD60A")
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown(f"<div class='sec-label'>| SUMBI PRESTIGE SCORE V3 / 100pts</div>", unsafe_allow_html=True)
    st.markdown(f\"\"\"<div style='text-align:center;padding:20px;border:2px solid {gc};border-radius:16px;margin:12px 0;'>
<div style='font-size:48px;font-weight:700;color:{gc};'>{v3_tot}</div>
<div style='color:#aaa;'>/100 {v3_grd} {v3_lbl}</div></div>\"\"\", unsafe_allow_html=True)
    labels = [
        ("flow",   "Money Flow",    25),
        ("chart",  "Chart Tech",    25),
        ("fundamental","Fundamental",13),
        ("news",   "News Momentum", 10),
        ("short",  "Short Signal",   8),
        ("macro",  "Macro Env",      7),
        ("sector", "Sector Theme",   7),
        ("broker", "Broker Flow",    5),
    ]
    rows = []
    for key, eng, max_s in labels:
        val, mx, _ = v3_bd.get(key, (0, max_s, {}))
        pct = int(val / mx * 100) if mx > 0 else 0
        bar_c = "#34C759" if pct >= 70 else "#FFD60A" if pct >= 40 else "#FF3B3B"
        rows.append(f\"\"\"<div style='background:rgba(255,255,255,0.03);border:1px solid #2a2a2a;border-radius:12px;padding:12px 16px;'>
<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;'>
<span style='font-size:13px;color:#e0e0e0;'>{eng}</span>
<span style='font-family:JetBrains Mono,monospace;font-size:14px;color:{bar_c};font-weight:700;'>{val}<span style='color:#52525b;font-size:10px;'>/{mx}</span></span>
</div>
<div style='background:#1a1a1a;border-radius:4px;height:6px;'>
<div style='background:{bar_c};width:{pct}%;height:6px;border-radius:4px;'></div>
</div></div>\"\"\")
    st.markdown(f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0;'>{''.join(rows)}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

"""

if target in content:
    content = content.replace(target, v3_ui + target, 1)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS!')
else:
    print('Target not found - checking line 622:')
    lines = content.split('\n')
    print(lines[621][:80])
