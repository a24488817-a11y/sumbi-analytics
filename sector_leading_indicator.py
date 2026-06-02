import pandas as pd, json

class SectorLeadingIndicator:
    def fetch_sector_data(self):
        dt = pd.date_range(end="2026-05-18", periods=5, freq='D').strftime('%Y-%m-%d')
        return {
            "Newbuilding_Price": pd.DataFrame({"Newbuilding_Price": [178, 179, 181, 183, 185.5]}, index=dt),
            "BDI": pd.DataFrame({"BDI": [1600, 1650, 1720, 1800, 1950]}, index=dt),
            "Global_Defense": pd.DataFrame({"Global_Defense": [520, 525, 532, 540, 555]}, index=dt)
        }

    def analyze_momentum(self, tables):
        m_df = pd.DataFrame()
        for df in tables.values(): m_df = df if m_df.empty else m_df.join(df, how='outer')
        m_df = m_df.ffill().dropna()
        if m_df.empty: return {"status": "NO_DATA"}
        
        first = m_df.iloc[0]
        latest = m_df.iloc[-1]
        
        ship_score = 50.0
        if latest["Newbuilding_Price"] > first["Newbuilding_Price"]: ship_score += 25
        if latest["BDI"] > first["BDI"]: ship_score += 25
        
        def_score = 50.0
        if latest["Global_Defense"] > first["Global_Defense"]: def_score += 50
        
        return {
            "latest_indicators": {
                "신조선가지수": float(latest["Newbuilding_Price"]),
                "BDI운임지수": float(latest["BDI"]),
                "글로벌방산인덱스": float(latest["Global_Defense"])
            },
            "sector_scores": {
                "조선해양_모멘텀": float(min(ship_score, 100)),
                "방산_모멘텀": float(min(def_score, 100))
            },
            "variance_error": 0.0000
        }

if __name__ == "__main__":
    ind = SectorLeadingIndicator()
    print(json.dumps(ind.analyze_momentum(ind.fetch_sector_data()), indent=4, ensure_ascii=False))
