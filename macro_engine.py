import pandas as pd
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

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import requests

class MacroShockEngine:
    def __init__(self, fred_api_key: str):
        self.fred_api_key = fred_api_key
        self.end_date = datetime.today().strftime('%Y-%m-%d')
        self.start_date = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')

    def get_fred_data(self, series_id: str) -> pd.Series:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={self.fred_api_key}&file_type=json"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                observations = data.get('observations', [])
                df = pd.DataFrame(observations)
                df['date'] = pd.to_datetime(df['date'])
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                df = df.ffill().bfill().set_index('date')
                return df['value']
            else:
                return pd.Series(dtype='float64')
        except Exception:
            return pd.Series(dtype='float64')

    def get_yfinance_data(self, ticker: str) -> pd.Series:
        try:
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(start=self.start_date, end=self.end_date)
            if not df.empty:
                return df['Close']
            return pd.Series(dtype='float64')
        except Exception:
            return pd.Series(dtype='float64')

    def aggregate_macro_metrics(self) -> pd.DataFrame:
        us_10y_bond = self.get_fred_data('DGS10')
        usd_krw_fred = self.get_fred_data('DEXKOUS')
        dollar_index = self.get_yfinance_data('DX-Y.NYB')
        bdi_index = self.get_yfinance_data('CL=F')
        
        macro_df = pd.DataFrame({
            'US_10Y_Bond': us_10y_bond,
            'Dollar_Index': dollar_index,
            'USD_KRW': usd_krw_fred,
            'BDI_Index': bdi_index
        })
        
        macro_df = macro_df.ffill().ffill().bfill()
        return macro_df