import re
with open("main.py", "r", encoding="utf-8") as f:
    code = f.read()

replacement = """def get_macro_data(_engine):
    try:
        import pandas as pd
        df = _engine.aggregate_macro_metrics()
        res = {}
        if df is not None and not df.empty:
            df = df.ffill().bfill()
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            for col in df.columns:
                try: val = float(latest[col])
                except: val = 0.0
                try: pval = float(prev[col])
                except: pval = 0.0
                res[str(col)] = val
                res[f"{col}_delta"] = val - pval
                
                c = str(col).lower()
                if '10' in c or 'bond' in c: res['us_10y_bond'] = val; res['us_10y_bond_delta'] = val - pval
                elif 'dollar' in c or 'dx' in c: res['dollar_index'] = val; res['dollar_index_delta'] = val - pval
                elif 'krw' in c or 'usd' in c: res['usd_krw'] = val; res['usd_krw_delta'] = val - pval
                elif 'bdi' in c or 'baltic' in c or 'cl' in c: res['bdi_index'] = val; res['bdi_index_delta'] = val - pval
        return res
    except Exception as e:
        import streamlit as st
        st.error(f"������ 엔진 백그라운드 에러: {e}")
        return {}
"""

# 완벽하고 안전한 함수 교체
code = re.sub(r"def get_macro_data.*?(?=_engine\s*=\s*get_macro_engine)", replacement + "\n", code, flags=re.DOTALL)

with open("main.py", "w", encoding="utf-8") as f:
    f.write(code)
