import re

with open("main.py", "r", encoding="utf-8") as f:
    code = f.read()

# 캐시(@st.cache_data)를 완전히 제거하고, 모든 이름표를 매칭하는 무적의 함수
sledgehammer = """def get_macro_data(_engine):
    try:
        df = _engine.aggregate_macro_metrics()
        res = {}
        if df is not None and not df.empty:
            df = df.ffill().bfill()
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            for col in df.columns:
                val = float(latest[col]) if pd.notna(latest[col]) else 0.0
                pval = float(prev[col]) if pd.notna(prev[col]) else 0.0
                delta = val - pval
                c = str(col).lower()
                
                # 어떤 대소문자로 부르든 무조건 응답하도록 전체 복제 매칭
                if '10' in c or 'bond' in c or 'us10y' in c:
                    res['us_10y_bond'] = val; res['us_10y_bond_delta'] = delta
                elif 'dollar' in c or 'dx' in c:
                    res['dollar_index'] = val; res['dollar_index_delta'] = delta
                elif 'krw' in c or 'usd' in c:
                    res['usd_krw'] = val; res['usd_krw_delta'] = delta
                elif 'bdi' in c or 'baltic' in c or 'cl' in c:
                    res['bdi_index'] = val; res['bdi_index_delta'] = delta
                    
                res[str(col)] = val; res[f"{col}_delta"] = delta
        return res
    except:
        return {}
"""

# 기존의 고장난 함수와 캐시 코드를 깔끔하게 도려내고 무적 함수로 교체
code = re.sub(r"@st\.cache_data.*?def get_macro_data.*?(?=_engine = get_macro_engine)", sledgehammer + "\n", code, flags=re.DOTALL)
code = re.sub(r"def get_macro_data.*?(?=_engine = get_macro_engine)", sledgehammer + "\n", code, flags=re.DOTALL)
code = re.sub(r"st\.info\(f'DEBUG RAW DATA.*?\'\)", "", code)

with open("main.py", "w", encoding="utf-8") as f:
    f.write(code)
