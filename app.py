import streamlit as st
from macro_engine import MacroShockEngine

st.title("Sumbi Analytics V1.0")
st.markdown("---")

@st.cache_resource
def get_macro_engine():
    api_key = st.secrets.get("FRED_API_KEY", None)
    return MacroShockEngine(api_key=api_key)

@st.cache_data(ttl=1800)
def get_macro_data(_engine):
    return _engine.collect_all_metrics()

engine = get_macro_engine()
macro_data = get_macro_data(engine)

us10 = macro_data.get("us_10y_bond", 0.0)
us10_d = macro_data.get("us_10y_bond_delta", 0.0)
dxy = macro_data.get("dollar_index", 0.0)
dxy_d = macro_data.get("dollar_index_delta", 0.0)
krw = macro_data.get("usd_krw", 0.0)
krw_d = macro_data.get("usd_krw_delta", 0.0)
bdi = macro_data.get("bdi_index", 0)
bdi_d = macro_data.get("bdi_index_delta", 0)

st.subheader("[Macro Shock Radar]")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("US 10Y Bond", f"{us10:.3f}%", f"{us10_d:+.3f}%")
with col2:
    st.metric("Dollar Index", f"{dxy:.2f}", f"{dxy_d:+.2f}")
with col3:
    st.metric("USD/KRW", f"{krw:,.1f}", f"{krw_d:+.1f}")
with col4:
    st.metric("BDI Index", f"{bdi:,} pt", f"{bdi_d:+d} pt")
st.markdown("---")
