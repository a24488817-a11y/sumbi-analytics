import re

with open("main.py", "r", encoding="utf-8") as f:
    code = f.read()

new_func = """@st.cache_data(ttl=1800)
def get_macro_data(_engine):
    try:
        df = _engine.aggregate_macro_metrics()
        res = {}
        if df is not None and not df.empty:
            df = df.ffill().bfill()
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            for col in df.columns:
                res[str(col)] = float(latest[col]) if pd.notna(latest[col]) else 0.0
                res[f"{col}_delta"] = float(latest[col]) - float(prev[col]) if pd.notna(prev[col]) else 0.0
        res["DEBUG_STATUS"] = "SUCCESS"
        return res
    except Exception as e:
        return {"DEBUG_STATUS": str(e)}
"""

code = re.sub(r"@st\.cache_data\(ttl=1800\)\ndef get_macro_data\(_engine\):.*?_engine = get_macro_engine\(\)", new_func + "\n_engine = get_macro_engine()", code, flags=re.DOTALL)

inject_str = "_m_data = get_macro_data(_engine)\nimport streamlit as st\nst.info(f'DEBUG RAW DATA: {_m_data}')"
if "DEBUG RAW DATA" not in code:
    code = code.replace("_m_data = get_macro_data(_engine)", inject_str)

with open("main.py", "w", encoding="utf-8") as f:
    f.write(code)
