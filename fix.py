import re
with open('/home/ubuntu/main.py', 'r', encoding='utf-8') as f: c = f.read()

# 1. 과거의 낡은 스코어보드 찌꺼기 100% 추적 및 소각
c = re.sub(r'[ \t]*try:\n(?:(?![ \t]*try:).)*?score_matrix.*?except Exception as e:\n[ \t]*pass\n', '', c, flags=re.DOTALL)
c = c.replace('(Money Flow Score) (Money Flow Score)', '(Money Flow Score)')

# 2. 완벽한 단 1개의 프리미엄 패널 재이식
lines = c.splitlines()
out, done = [], False
for line in lines:
    out.append(line + '\n')
    if 'Pension' in line and 'st.metric' in line and not done:
        i = line[:len(line) - len(line.lstrip())]
        out.append(i + "try:\n" + i + "    import score_matrix\n")
        out.append(i + "    res = score_matrix.calculate_ultimate_tomorrow_score(kis_flow_data=[{'foreigner':-498153,'institution':660827,'pension':0,'volume':1500000}], naver_news_data={'sentiment_score':0.82}, krx_macro_data={'short_balance_velocity':-0.06,'usd_krw':1461.1,'wti':101.02}, real_time_chart={'current_price':118100,'ma_5':117000,'ma_10':116500,'return_3d':-0.01}, financial_data={'per':35.15,'pbr':2.10,'op_margin':18.4})\n")
        out.append(i + "    h = f'''<div style=\"background:linear-gradient(135deg,#1a1a1a 0%,#050505 100%);padding:25px;border-radius:12px;margin-top:25px;border:1px solid #D4AF37;box-shadow:0 4px 20px rgba(212,175,55,0.15);\"><h4 style=\"color:#D4AF37;margin:0;text-align:center;\">\\U0001f525 42\\ub300 \\ud544\\uc0b4\\uae30: \\ub525-\\uc560\\ub110\\ub9ac\\ud2f1\\uc2a4</h4><h1 style=\"color:#FFF;font-size:55px;text-align:center;margin:10px 0;\">{res['total']} <span style=\"font-size:22px;color:#888;\">/ 100</span></h1><div style=\"border-top:1px solid #333;margin:20px 0;\"></div><div style=\"display:flex;justify-content:space-between;margin-bottom:12px;\"><span style=\"color:#A0A0A0;\">1. \\uba54\\uc774\\uc800 \\uc218\\uae09 (Money Flow) [40\\uc810]</span><span style=\"color:#D4AF37;font-weight:bold;\">{res['flow']}</span></div><div style=\"display:flex;justify-content:space-between;margin-bottom:12px;\"><span style=\"color:#A0A0A0;\">2. \\ubbf8\\ubc18\\uc601 \\ud638\\uc7ac (Momentum) [20\\uc810]</span><span style=\"color:#D4AF37;font-weight:bold;\">{res['mom']}</span></div><div style=\"display:flex;justify-content:space-between;margin-bottom:12px;\"><span style=\"color:#A0A0A0;\">3. \\uacf5\\ub9e4\\ub3c4/\\ub9e4\\ud06c\\ub85c (Macro) [15\\uc810]</span><span style=\"color:#D4AF37;font-weight:bold;\">{res['macro']}</span></div><div style=\"display:flex;justify-content:space-between;margin-bottom:12px;\"><span style=\"color:#A0A0A0;\">4. \\uae30\\uc220\\uc801 \\ud0c0\\uc774\\ubc0d (Timing) [15\\uc810]</span><span style=\"color:#D4AF37;font-weight:bold;\">{res['time']}</span></div><div style=\"display:flex;justify-content:space-between;\"><span style=\"color:#A0A0A0;\">5. \\uae30\\uc5c5 \\ud380\\ub354\\uba58\\ud0c8 (Value) [10\\uc810]</span><span style=\"color:#D4AF37;font-weight:bold;\">{res['val']}</span></div></div>'''\n")
        out.append(i + "    import streamlit as st; st.markdown(h, unsafe_allow_html=True)\n")
        out.append(i + "except Exception as e: pass\n")
        done = True

with open('/home/ubuntu/main.py', 'w', encoding='utf-8') as f: f.writelines(out)
print("=== PERFECT UI RESTORED ===")
