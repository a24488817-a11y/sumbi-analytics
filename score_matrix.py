import pandas as pd
import numpy as np

def calculate_ultimate_tomorrow_score(kis_flow_data, naver_news_data, krx_macro_data, real_time_chart, financial_data):
    score_flow, score_mom, score_macro, score_time, score_val = 15.0, 10.0, 7.0, 5.0, 5.0
    try:
        df_flow = pd.DataFrame(kis_flow_data)
        c_frgn, c_inst, c_pnsn = df_flow['foreigner'].iloc[-1], df_flow['institution'].iloc[-1], df_flow['pension'].iloc[-1]
        m_frgn, s_frgn = df_flow['foreigner'].mean(), df_flow['foreigner'].std() + 1e-9
        m_inst, s_inst = df_flow['institution'].mean(), df_flow['institution'].std() + 1e-9
        z_frgn, z_inst = (c_frgn - m_frgn) / s_frgn, (c_inst - m_inst) / s_inst
        sf = 25.0 if (z_frgn > 1.0 and z_inst > 1.0) else (15.0 if (z_frgn > 0.5 or z_inst > 0.5) else 0.0)
        if c_pnsn > 0: sf += 10.0
        if df_flow['volume'].iloc[-1] / (df_flow['volume'].mean() + 1e-9) >= 1.5: sf += 5.0
        score_flow = min(40.0, max(0.0, sf))
    except: pass
    try:
        ns = float(naver_news_data.get('sentiment_score', 0.5))
        r3 = float(real_time_chart.get('return_3d', 0.0))
        div = ns - (r3 * 2.0)
        score_mom = 20.0 if div > 0.5 else (14.0 if div > 0.2 else 8.0)
    except: pass
    try:
        sb = float(krx_macro_data.get('short_balance_velocity', 0.0))
        fx = float(krx_macro_data.get('usd_krw', 1350.0))
        wti = float(krx_macro_data.get('wti', 75.0))
        sm = 10.0 if sb < -0.05 else 5.0
        if fx >= 1450.0 or wti >= 100.0: sm -= 5.0
        score_macro = min(15.0, max(0.0, sm))
    except: pass
    try:
        cp = float(real_time_chart.get('current_price', 1.0))
        m5 = float(real_time_chart.get('ma_5', 1.0))
        m10 = float(real_time_chart.get('ma_10', 1.0))
        d5, d10 = (cp - m5) / m5, (cp - m10) / m10
        if (0.005 <= d5 <= 0.02) or (0.005 <= d10 <= 0.02): score_time = 15.0
        elif m5 > m10 and d5 > 0: score_time = 10.0
        else: score_time = 5.0
    except: pass
    try:
        per = float(financial_data.get('per', 999.0))
        pbr = float(financial_data.get('pbr', 9.9))
        op = float(financial_data.get('op_margin', 0.0))
        sv = 6.0 if (pbr < 1.2 and per < 15.0) else 3.0
        sv += 4.0 if op >= 15.0 else 2.0
        score_val = min(10.0, max(0.0, sv))
    except: pass
    
    # 딕셔너리 형태로 모든 세부 데이터 정밀 분해 반환
    return {
        'total': round(score_flow + score_mom + score_macro + score_time + score_val, 1),
        'flow': round(score_flow, 1),
        'mom': round(score_mom, 1),
        'macro': round(score_macro, 1),
        'time': round(score_time, 1),
        'val': round(score_val, 1)
    }
