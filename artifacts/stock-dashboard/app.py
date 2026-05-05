import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pykrx import stock
from datetime import datetime, timedelta

st.set_page_config(
    page_title="KRX Stock Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 KRX Stock Dashboard")
st.caption("Korean Exchange (KRX) market data powered by pykrx")

@st.cache_data(ttl=300)
def get_market_ticker_list(market):
    try:
        today = datetime.today().strftime("%Y%m%d")
        tickers = stock.get_market_ticker_list(today, market=market)
        names = {t: stock.get_market_ticker_name(t) for t in tickers[:200]}
        return names
    except Exception as e:
        st.error(f"Failed to load ticker list: {e}")
        return {}

@st.cache_data(ttl=300)
def get_ohlcv(ticker, start, end):
    try:
        df = stock.get_market_ohlcv_by_date(start, end, ticker)
        return df
    except Exception as e:
        st.error(f"Failed to load OHLCV data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_market_cap(ticker, start, end):
    try:
        df = stock.get_market_cap_by_date(start, end, ticker)
        return df
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_market_ohlcv_all(date, market):
    try:
        df = stock.get_market_ohlcv_by_ticker(date, market=market)
        return df
    except Exception as e:
        return pd.DataFrame()

with st.sidebar:
    st.header("Settings")
    market = st.selectbox("Market", ["KOSPI", "KOSDAQ", "KONEX"], index=0)

    end_date = datetime.today()
    start_date = end_date - timedelta(days=90)

    date_range = st.date_input(
        "Date Range",
        value=(start_date.date(), end_date.date()),
        max_value=end_date.date()
    )
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_str = date_range[0].strftime("%Y%m%d")
        end_str = date_range[1].strftime("%Y%m%d")
    else:
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")

    st.divider()
    st.subheader("Stock Lookup")
    with st.spinner("Loading ticker list..."):
        tickers_dict = get_market_ticker_list(market)

    if tickers_dict:
        ticker_options = [f"{name} ({code})" for code, name in tickers_dict.items()]
        ticker_map = {f"{name} ({code})": code for code, name in tickers_dict.items()}
        selected_label = st.selectbox("Select Stock", ticker_options)
        selected_ticker = ticker_map[selected_label]
        selected_name = tickers_dict[selected_ticker]
    else:
        selected_ticker = None
        selected_name = ""

tab1, tab2, tab3 = st.tabs(["📊 Stock Analysis", "🏆 Market Overview", "📋 Market Snapshot"])

with tab1:
    if selected_ticker:
        st.subheader(f"{selected_name} ({selected_ticker})")

        col1, col2 = st.columns([2, 1])

        with st.spinner("Loading stock data..."):
            df_ohlcv = get_ohlcv(selected_ticker, start_str, end_str)
            df_cap = get_market_cap(selected_ticker, start_str, end_str)

        if not df_ohlcv.empty:
            latest = df_ohlcv.iloc[-1]
            prev = df_ohlcv.iloc[-2] if len(df_ohlcv) > 1 else latest
            change = latest["종가"] - prev["종가"]
            change_pct = (change / prev["종가"]) * 100 if prev["종가"] != 0 else 0

            with col1:
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Close", f"{latest['종가']:,.0f}", f"{change:+,.0f} ({change_pct:+.2f}%)")
                m2.metric("Open", f"{latest['시가']:,.0f}")
                m3.metric("High", f"{latest['고가']:,.0f}")
                m4.metric("Low", f"{latest['저가']:,.0f}")

            with col2:
                vol_change = latest["거래량"] - prev["거래량"]
                st.metric("Volume", f"{latest['거래량']:,.0f}", f"{vol_change:+,.0f}")
                if not df_cap.empty:
                    cap_latest = df_cap.iloc[-1]
                    st.metric("Market Cap", f"₩{cap_latest['시가총액']/1e12:.2f}T")

            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df_ohlcv.index,
                open=df_ohlcv["시가"],
                high=df_ohlcv["고가"],
                low=df_ohlcv["저가"],
                close=df_ohlcv["종가"],
                name="OHLCV",
                increasing_line_color="#FF4B4B",
                decreasing_line_color="#1E88E5"
            ))
            fig.update_layout(
                title=f"{selected_name} Candlestick Chart",
                xaxis_title="Date",
                yaxis_title="Price (KRW)",
                xaxis_rangeslider_visible=False,
                height=450,
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            fig_vol = px.bar(
                df_ohlcv,
                x=df_ohlcv.index,
                y="거래량",
                title="Trading Volume",
                color="거래량",
                color_continuous_scale="Blues",
                labels={"거래량": "Volume", "x": "Date"}
            )
            fig_vol.update_layout(height=250, template="plotly_white", showlegend=False)
            st.plotly_chart(fig_vol, use_container_width=True)

            with st.expander("Raw Data"):
                st.dataframe(df_ohlcv.sort_index(ascending=False), use_container_width=True)
        else:
            st.warning("No data available for the selected date range.")
    else:
        st.info("Select a stock from the sidebar to view analysis.")

with tab2:
    st.subheader(f"{market} Market Overview")
    with st.spinner("Loading market data..."):
        snap_date = end_str
        df_all = get_market_ohlcv_all(snap_date, market)

    if not df_all.empty:
        df_all = df_all.reset_index()
        name_col = "티커" if "티커" in df_all.columns else df_all.columns[0]

        col_a, col_b, col_c = st.columns(3)
        if "등락률" in df_all.columns:
            gainers = df_all[df_all["등락률"] > 0]
            losers = df_all[df_all["등락률"] < 0]
            col_a.metric("Total Stocks", len(df_all))
            col_b.metric("Gainers", len(gainers), delta=f"+{len(gainers)}", delta_color="normal")
            col_c.metric("Losers", len(losers), delta=f"-{len(losers)}", delta_color="inverse")

            fig_dist = px.histogram(
                df_all,
                x="등락률",
                nbins=50,
                title=f"{market} Daily Return Distribution",
                labels={"등락률": "Change (%)"},
                color_discrete_sequence=["#636EFA"]
            )
            fig_dist.add_vline(x=0, line_dash="dash", line_color="gray")
            fig_dist.update_layout(template="plotly_white", height=350)
            st.plotly_chart(fig_dist, use_container_width=True)

        if "등락률" in df_all.columns and "거래량" in df_all.columns:
            top_gainers = df_all.nlargest(10, "등락률")[["티커", "종가", "등락률", "거래량"]] if "티커" in df_all.columns else df_all.nlargest(10, "등락률")
            top_losers = df_all.nsmallest(10, "등락률")[["티커", "종가", "등락률", "거래량"]] if "티커" in df_all.columns else df_all.nsmallest(10, "등락률")

            col_left, col_right = st.columns(2)
            with col_left:
                st.subheader("🔴 Top Gainers")
                st.dataframe(top_gainers, use_container_width=True)
            with col_right:
                st.subheader("🔵 Top Losers")
                st.dataframe(top_losers, use_container_width=True)
    else:
        st.warning(f"No market data available for {snap_date}. Try a different date range.")

with tab3:
    st.subheader(f"{market} Market Snapshot")
    if not df_all.empty:
        st.write(f"Data as of **{snap_date}** — {len(df_all)} stocks")

        if "거래량" in df_all.columns:
            top_volume = df_all.nlargest(20, "거래량")
            fig_top = px.bar(
                top_volume,
                x="티커" if "티커" in top_volume.columns else top_volume.columns[0],
                y="거래량",
                title="Top 20 Stocks by Trading Volume",
                color="등락률" if "등락률" in top_volume.columns else None,
                color_continuous_scale="RdBu",
                labels={"거래량": "Volume", "티커": "Ticker"}
            )
            fig_top.update_layout(template="plotly_white", height=400)
            st.plotly_chart(fig_top, use_container_width=True)

        st.dataframe(df_all, use_container_width=True, height=400)
    else:
        st.info("Market snapshot data not available.")
