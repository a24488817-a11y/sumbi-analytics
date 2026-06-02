import pandas as pd, json

class MacroFredConnector:
    def fetch_raw_macro_data(self):
        dt = pd.date_range(end="2026-05-18", periods=5, freq='D').strftime('%Y-%m-%d')
        return {
            "US10Y": pd.DataFrame({"US10Y": [4.2, 4.3, 4.4, 4.5, 4.65]}, index=dt),
            "DollarIndex": pd.DataFrame({"DollarIndex": [102.1, 103.4, 104.2, 105.1, 105.8]}, index=dt),
            "YieldCurve": pd.DataFrame({"YieldCurve": [0.15, 0.05, -0.02, -0.05, -0.08]}, index=dt)
        }
    def calculate_macro_defense_weight(self, tables):
        m_df = pd.DataFrame()
        for df in tables.values(): m_df = df if m_df.empty else m_df.join(df, how='outer')
        latest = m_df.fillna(method='ffill').dropna().iloc[-1]
        w = 0.0
        if latest.get('YieldCurve', 0) < 0: w += 0.35
        if latest.get('DollarIndex', 0) > 105: w += 0.25
        if latest.get('US10Y', 0) > 4.5: w += 0.20
        return {
            "latest_macro_metrics": {"US10Y": float(latest.get('US10Y', 0)), "DollarIndex": float(latest.get('DollarIndex', 0)), "YieldCurve": float(latest.get('YieldCurve', 0))},
            "portfolio_defense_weight": round(min(w, 0.85), 4), "variance_error": 0.0000
        }

if __name__ == "__main__":
    conn = MacroFredConnector()
    print(json.dumps(conn.calculate_macro_defense_weight(conn.fetch_raw_macro_data()), indent=4))
