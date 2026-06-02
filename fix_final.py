import re

with open("macro_engine.py", "r", encoding="utf-8") as f:
    m_code = f.read()

patch = """import pandas as pd
_orig_df = pd.DataFrame
def _safe_df(data=None, *args, **kwargs):
    if isinstance(data, dict):
        sd = {}
        for k, v in data.items():
            if isinstance(v, pd.Series) and hasattr(v.index, 'tz') and getattr(v.index, 'tz', None) is not None:
                sd[k] = v.tz_localize(None)
            else:
                sd[k] = v
        data = sd
    return _orig_df(data, *args, **kwargs)
pd.DataFrame = _safe_df
"""
if "_safe_df" not in m_code:
    m_code = patch + "\n" + m_code
with open("macro_engine.py", "w", encoding="utf-8") as f:
    f.write(m_code)

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
            col_map = {}
            for c in df.columns:
                cl = str(c).lower()
                if '10' in cl or 'bond' in cl or 'dgs' in cl: col_map[c] = 'us_10y_bond'
                elif 'dollar' in cl or 'dx' in cl or 'dxy' in cl: col_map[c] = 'dollar_index'
                elif 'krw' in cl or 'usd' in cl or '환율' in cl: col_map[c] = 'usd_krw'
                elif 'bdi' in cl or 'baltic' in cl: col_map[c] = 'bdi_index'
            for col in df.columns:
                val = float(latest[col]) if pd.notna(latest[col]) else 0.0
                pval = float(prev[col]) if pd.notna(prev[col]) else val
                mapped_k = col_map.get(col, str(col))
                res[mapped_k] = val
                res[f"{mapped_k}_delta"] = val - pval
        return res
    except Exception as e:
        return {}
"""
code = re.sub(r"@st\.cache_data\(ttl=1800\)\ndef get_macro_data\(_engine\):.*?_engine = get_macro_engine\(\)", new_func + "\n_engine = get_macro_engine()", code, flags=re.DOTALL)

with open("main.py", "w", encoding="utf-8") as f:
    f.write(code)
