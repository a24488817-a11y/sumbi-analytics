with open('/home/ubuntu/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

v3_ui = """
# V3 점수판 UI
if "v3_result" in dir() and v3_result:
    v3 = v3_result
    v3_tot = v3["total"]
    v3_grd = v3["grade"]
    v3_lbl = v3["grade_label"]
    v3_brk = v3["breakdown"]
    gc = {"S+":"#00FF94","S":"#34C759","A+":"#FFD60A","A":"#FFD60A","B":"#FF9500","C":"#FF6B35","D":"#FF3B3B"}.get(v3_grd,"#FFD60A")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(f'<div class="sec-label">| SUMBI SCORE V3 <span class="sec-sub">/ 8 Items 100pts</span></div>', unsafe_allow_html=True)
    st.markdown(f\"""
    <div style='background:rgba(0,0,0,0.4);border:2px solid {gc}60;border-radius:20px;padding:24px;margin:12px 0;'>
        <div style='font-family:JetBrains Mono,monospace;font-size:11px;color:#52525b;letter-spacing:.2em;'>SUMBI PRESTIGE SCORE V3 / 숨비 종합 투자 점수</div>
        <div style='display:flex;align-items:baseline;gap:12px;margin:8px 0;'>
            <span style='font-family:Cormorant Garamond,serif;font-size:56px;color:{gc};font-weight:700;line-height:1;'>{v3_tot}</span>
            <span style='font-size:18px;color:#52525b;'>/100</span>
            <span style='background:{gc}20;border:1px solid {gc}60;border-radius:8px;padding:4px 14px;font-family:JetBrains Mono,monospace;font-size:14px;color:{gc};font-weight:700;'>{v3_grd}</span>
        </div>
        <div style='font-size:14px;color:#a0a0a0;'>{v3_lbl}</div>
    </div>\""", unsafe_allow_html=True)
    labels = [
        ("flow",        "Money Flow",   "메이저 수급",   25),
        ("chart",       "Chart Tech",   "차트 기술적",   25),
        ("fundamental", "Fundamental",  "기업 펀더멘털", 13),
        ("news",        "News",         "뉴스 모멘텀",   10),
        ("short",       "Short Signal", "공매도 신호",    8),
        ("macro",       "Macro Env",    "매크로 환경",    7),
        ("sector",      "Sector",       "섹터 테마",      7),
        ("broker",      "Broker Flow",  "거래원 분석",    5),
    ]
    rows = []
    for key, eng, kor, mx in labels:
        val, _, _ = v3_brk.get(key, (0, mx, {}))
        pct = int(val / mx * 100) if mx > 0 else 0
        bc = "#34C759" if pct >= 70 else "#FFD60A" if pct >= 40 else "#FF3B3B"
        rows.append(f"<div style='background:rgba(255,255,255,0.03);border:1px solid #2a2a2a;border-radius:12px;padding:12px 16px;'><div style='display:flex;justify-content:space-between;margin-bottom:6px;'><span style='font-size:13px;color:#e0e0e0;'>{eng} <span style='color:#52525b;font-size:11px;'>/ {kor}</span></span><span style='font-family:JetBrains Mono,monospace;font-size:14px;color:{bc};font-weight:700;'>{val}<span style='color:#52525b;font-size:10px;'>/{mx}</span></span></div><div style='background:#1a1a1a;border-radius:4px;height:6px;'><div style='background:{bc};width:{pct}%;height:6px;border-radius:4px;'></div></div></div>")
    st.markdown(f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0;'>{''.join(rows)}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
"""

target = 'st.markdown(\'<div class="sec-label">| QUANT FLOW MATRIX'
if target in content:
    content = content.replace(target, v3_ui + "\n" + target, 1)
    with open('/home/ubuntu/main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS!")
else:
    for i, line in enumerate(content.split('\n')):
        if 'QUANT FLOW' in line:
            print(f"Found: {i+1}: {line[:60]}")
