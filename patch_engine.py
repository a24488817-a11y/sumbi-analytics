import streamlit as st
if 'captured_org' not in st.session_state: st.session_state['captured_org'] = 0
if 'captured_frgn' not in st.session_state: st.session_state['captured_frgn'] = 0
def custom_metric_engine(label, value, delta=None, delta_color='normal', help=None, label_visibility='visible'):
    lbl, v_str = str(label), str(value)
    def parse_num(s):
        c = ''.join([x for x in s if x.isdigit() or x == '-'])
        try: return int(c)
        except: return 0
    if '\uae30\uad00' in lbl: st.session_state['captured_org'] = parse_num(v_str)
    elif '\uc678\uad6d\uc778' in lbl: st.session_state['captured_frgn'] = parse_num(v_str)
    elif '\uac1c\uc778' in lbl:
        if parse_num(v_str) == 0:
            calc = -(st.session_state['captured_org'] + st.session_state['captured_frgn'])
            value, v_str = f'{calc:,}\uc8fc', f'{calc:,}\uc8fc'
    d_str = str(delta) if delta else ''
    sign = 0
    if d_str and d_str != 'None' and d_str.strip():
        if '-' in d_str: sign = -1
        elif '+' in d_str: sign = 1
        else:
            try:
                if float(''.join([x for x in d_str if x.isdigit() or x == '.'])) > 0: sign = 1
            except: pass
    else:
        if '-' in v_str: sign = -1
        elif '0\uc8fc' in v_str or v_str.strip() == '0': sign = 0
        else:
            try:
                if float(''.join([x for x in v_str if x.isdigit() or x == '.'])) > 0: sign = 1
            except: pass
    color, arrow_char = '#A0A0A0', '\u2500'
    if sign > 0: color, arrow_char = '#FF4B4B', '\u25b2'
    elif sign < 0: color, arrow_char = '#1E88E5', '\u25bc'
    badge = ''
    v_num = abs(parse_num(v_str))
    if '\ud658\uc728' in lbl and v_num >= 1450: badge = ' <span style="background-color:#FF4B4B; color:white; padding:2px 6px; font-size:11px; font-weight:bold; border-radius:4px; margin-left:8px;">\u26a0\ufe0f \uace0\ud658\uc728 \ud22c\uc790\uc8fc\uc758</span>'
    elif 'WTI' in lbl and v_num >= 100: badge = ' <span style="background-color:#D4AF37; color:black; padding:2px 6px; font-size:11px; font-weight:bold; border-radius:4px; margin-left:8px;">\U0001f525 \uc720\uac00 \ud3ed\ub4f1 \uacbd\uace0</span>'
    card_text_color = color if sign != 0 else '#FFFFFF'
    arrow_html = f'<div style="color: {color}; font-size: 14px; font-weight: bold; margin-top: 3px;">{arrow_char} {delta}</div>' if (delta and str(delta).strip() and str(delta) != 'None') else ''
    html_layout = f'<div style="background-color: #1E1E1E; padding: 14px; border-radius: 8px; border-left: 5px solid {color}; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"><div style="color: #A0A0A0; font-size: 13px; font-weight: 500; display: flex; align-items: center; font-family: \'Malgun Gothic\', sans-serif;">{label}{badge}</div><div style="color: {card_text_color}; font-size: 25px; font-weight: bold; margin-top: 5px; font-family: \'Helvetica Neue\', sans-serif;">{value}</div>{arrow_html}</div>'
    st.markdown(html_layout, unsafe_allow_html=True)
st.metric = custom_metric_engine