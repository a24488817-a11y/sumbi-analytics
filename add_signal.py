with open('/home/ubuntu/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

ai_panel = """
# AI 투자신호 패널
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown(f'<div class="sec-label">| AI MACRO SIGNAL <span class="sec-sub">/ 인공지능 거시경제 투자신호</span></div>', unsafe_allow_html=True)

if macro:
    _wti = macro.get("wti")
    _krw = macro.get("krw")
    _dxy = macro.get("dxy")
    _tnx = macro.get("tnx")
    _score = 0
    _warns = []
    _goods = []

    if _wti:
        if _wti > 95: _score -= 3; _warns.append(("WTI 고유가 위험", f"WTI {_wti:.1f}$ 인플레 압력", "#FF3B3B", "fire"))
        elif _wti > 80: _score -= 1; _warns.append(("WTI 유가 주의", f"WTI {_wti:.1f}$ 상단 경계", "#FF9500", "warning"))
        elif _wti < 60: _score += 2; _goods.append(("WTI 저유가 우호", f"WTI {_wti:.1f}$ 기업비용 감소", "#34C759", "check"))
        else: _goods.append(("WTI 유가 정상", f"WTI {_wti:.1f}$ 안정구간", "#30D158", "check"))

    if _krw:
        if _krw > 1450: _score -= 3; _warns.append(("환율 위험", f"KRW {_krw:.0f}원 외국인 이탈", "#FF3B3B", "fire"))
        elif _krw > 1380: _score -= 1; _warns.append(("환율 주의", f"KRW {_krw:.0f}원 원화약세", "#FF9500", "warning"))
        elif _krw < 1300: _score += 2; _goods.append(("원화 강세", f"KRW {_krw:.0f}원 외국인 유입", "#34C759", "check"))
        else: _goods.append(("환율 정상", f"KRW {_krw:.0f}원 정상범위", "#30D158", "check"))

    if _dxy:
        if _dxy > 107: _score -= 2; _warns.append(("달러 강세 위험", f"DXY {_dxy:.1f} 신흥국압박", "#FF3B3B", "fire"))
        elif _dxy > 103: _score -= 1; _warns.append(("달러 강세 주의", f"DXY {_dxy:.1f} 상단경계", "#FF9500", "warning"))
        elif _dxy < 98: _score += 2; _goods.append(("달러 약세 우호", f"DXY {_dxy:.1f} 매수여건", "#34C759", "check"))
        else: _goods.append(("달러 안정", f"DXY {_dxy:.1f} 중립구간", "#30D158", "check"))

    if _tnx:
        if _tnx > 4.8: _score -= 3; _warns.append(("금리 위험", f"10Y {_tnx:.2f}% 밸류압박", "#FF3B3B", "fire"))
        elif _tnx > 4.3: _score -= 1; _warns.append(("금리 주의", f"10Y {_tnx:.2f}% 상단부담", "#FF9500", "warning"))
        elif _tnx < 3.5: _score += 3; _goods.append(("금리 우호", f"10Y {_tnx:.2f}% 밸류개선", "#34C759", "check"))
        else: _goods.append(("금리 보통", f"10Y {_tnx:.2f}% 정상범위", "#30D158", "check"))

    if _score >= 5:
        _fi, _ft, _fd, _fc, _fbg = "STRONG BUY", "강력 매수 권고", "전 지표 우호. 적극 매수", "#00FF94", "rgba(0,255,148,0.08)"
        _img = "https://img.icons8.com/emoji/96/fire.png"
    elif _score >= 2:
        _fi, _ft, _fd, _fc, _fbg = "BUY", "매수 권고", "거시경제 긍정. 분할매수 권고", "#34C759", "rgba(52,199,89,0.08)"
        _img = "https://img.icons8.com/emoji/96/check-mark-button.png"
    elif _score >= -1:
        _fi, _ft, _fd, _fc, _fbg = "NEUTRAL", "중립 관망", "복합신호 혼재. 신중 관망", "#FFD60A", "rgba(255,214,10,0.08)"
        _img = "https://img.icons8.com/emoji/96/bar-chart.png"
    elif _score >= -4:
        _fi, _ft, _fd, _fc, _fbg = "CAUTION", "투자 주의", "불안정. 비중 축소 권고", "#FF9500", "rgba(255,149,0,0.08)"
        _img = "https://img.icons8.com/emoji/96/warning.png"
    else:
        _fi, _ft, _fd, _fc, _fbg = "DANGER", "투자 경고", "전 지표 위험. 즉각 비중 축소", "#FF3B3B", "rgba(255,59,59,0.08)"
        _img = "https://img.icons8.com/emoji/96/sos-button.png"

    st.markdown(f\\"\\"\\"
    <div style='background:{_fbg};border:1.5px solid {_fc}60;border-radius:16px;padding:20px 24px;margin:14px 0;display:flex;align-items:center;gap:20px;'>
        <img src='{_img}' style='width:60px;height:60px;flex-shrink:0;'/>
        <div style='flex:1;'>
            <div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#52525b;letter-spacing:.2em;margin-bottom:4px;'>AI MACRO SIGNAL / 인공지능 투자신호</div>
            <div style='font-family:Cormorant Garamond,serif;font-size:22px;color:{_fc};font-weight:600;margin-bottom:4px;'>{_fi} / {_ft}</div>
            <div style='font-size:12px;color:#a0a0a0;'>{_fd}</div>
            <div style='margin-top:8px;font-family:JetBrains Mono,monospace;font-size:10px;color:#52525b;'>MACRO SCORE : {_score:+d}</div>
        </div>
    </div>
    \\"\\"\\"\\", unsafe_allow_html=True)

    _all_cards = []
    for _t, _d, _c, _ico in _warns:
        _all_cards.append(f\\"<div style='background:rgba(255,59,59,0.05);border:1px solid {_c}40;border-radius:10px;padding:12px;flex:1;min-width:180px;'><div style='color:{_c};font-size:12px;font-weight:600;margin-bottom:3px;'>{_t}</div><div style='color:#a0a0a0;font-size:11px;'>{_d}</div></div>\\")
    for _t, _d, _c, _ico in _goods:
        _all_cards.append(f\\"<div style='background:rgba(52,199,89,0.05);border:1px solid {_c}40;border-radius:10px;padding:12px;flex:1;min-width:180px;'><div style='color:{_c};font-size:12px;font-weight:600;margin-bottom:3px;'>{_t}</div><div style='color:#a0a0a0;font-size:11px;'>{_d}</div></div>\\")
    if _all_cards:
        st.markdown(f\\"<div style='display:flex;flex-wrap:wrap;gap:8px;margin:8px 0;'>{''.join(_all_cards)}</div>\\", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

"""

target = "st.markdown('<div class=\"sec-label\">| GLOBAL MACRO CROSS RADAR"
if target in content:
    content = content.replace(target, ai_panel + "\n" + target, 1)
    with open('/home/ubuntu/main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: AI 투자신호 패널 추가 완료!")
else:
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'GLOBAL MACRO' in line:
            print(f"Found at line {i+1}: {line[:70]}")
