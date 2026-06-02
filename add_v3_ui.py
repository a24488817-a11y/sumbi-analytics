with open('/home/ubuntu/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

v3_ui = '''
# ================================================================
# SUMBI V3 점수판 UI
# ================================================================
if "v3_result" in dir():
    v3 = v3_result
    v3_total = v3["total"]
    v3_grade = v3["grade"]
    v3_label = v3["grade_label"]
    v3_bd = v3["breakdown"]

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

    st.markdown("<div class=\\"panel\\">", unsafe_allow_html=True)
    st.markdown(
        f"<div class=\\"sec-label\\">| SUMBI SCORE V3 "
        f"<span class=\\"sec-sub\\">/ 8개 항목 100점 종합평가</span></div>",
        unsafe_allow_html=True
    )

    # 메인 점수 카드
    st.markdown(f"""
    <div style='background:rgba(0,0,0,0.4);border:2px solid {gc}60;border-radius:20px;padding:24px;margin:12px 0;display:flex;align-items:center;gap:20px;'>
        <img src='{gi}' style='width:64px;height:64px;flex-shrink:0;'/>
        <div style='flex:1;'>
            <div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#52525b;letter-spacing:.2em;'>SUMBI PRESTIGE SCORE V3 / 숨비 종합 투자 점수</div>
            <div style='display:flex;align-items:baseline;gap:12px;margin:6px 0;'>
                <span style='font-family:Cormorant Garamond,serif;font-size:52px;color:{gc};font-weight:700;line-height:1;'>{v3_total}</span>
                <span style='font-size:18px;color:#52525b;'>/100</span>
                <span style='background:{gc}20;border:1px solid {gc}60;border-radius:8px;padding:4px 12px;font-family:JetBrains Mono,monospace;font-size:14px;color:{gc};font-weight:700;'>{v3_grade}</span>
            </div>
            <div style='font-size:14px;color:#a0a0a0;letter-spacing:.05em;'>{v3_label}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 8개 항목 세부 점수
    labels = [
        ("flow",        "������", "메이저 수급", "Money Flow",     25),
        ("chart",       "������", "차트 기술적", "Chart & Tech",   25),
        ("fundamental", "������", "기업 펀더멘털","Fundamental",   13),
        ("news",        "������", "뉴스 모멘텀", "News Momentum",  10),
        ("short",       "������️", "공매도 신호", "Short Signal",    8),
        ("macro",       "������", "매크로 환경", "Macro Env",        7),
        ("sector",      "������", "섹터 테마",   "Sector Theme",     7),
        ("broker",      "⚡", "거래원 분석", "Broker Flow",      5),
    ]

    rows = []
    for key, icon, kor, eng, max_s in labels:
        val, mx, _ = v3_bd.get(key, (0, max_s, {}))
        pct = int(val / mx * 100) if mx > 0 else 0
        if pct >= 70: bar_c = "#34C759"
        elif pct >= 40: bar_c = "#FFD60A"
        else: bar_c = "#FF3B3B"
        rows.append(f"""
        <div style='background:rgba(255,255,255,0.03);border:1px solid #2a2a2a;border-radius:12px;padding:12px 16px;'>
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;'>
                <span style='font-size:13px;color:#e0e0e0;'>{icon} {kor} <span style='color:#52525b;font-size:11px;'>/ {eng}</span></span>
                <span style='font-family:JetBrains Mono,monospace;font-size:14px;color:{bar_c};font-weight:700;'>{val}<span style='color:#52525b;font-size:10px;'>/{mx}</span></span>
            </div>
            <div style='background:#1a1a1a;border-radius:4px;height:6px;'>
                <div style='background:{bar_c};width:{pct}%;height:6px;border-radius:4px;'></div>
            </div>
        </div>""")

    # 4개씩 2줄로
    st.markdown(f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0;'>{''.join(rows)}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
'''

# QUANT FLOW MATRIX 섹션 앞에 삽입
target = "st.markdown('<div class=\\"sec-label\\">| QUANT FLOW MATRIX"
if target in content:
    content = content.replace(target, v3_ui + "\n" + target, 1)
    with open('/home/ubuntu/main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: V3 점수판 UI 추가 완료!")
else:
    # 위치 찾기
    for i, line in enumerate(content.split('\n')):
        if 'QUANT FLOW' in line:
            print(f"Found: {i+1}줄: {line[:60]}")
