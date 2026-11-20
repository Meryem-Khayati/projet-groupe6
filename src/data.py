"""data.py - Telechargement (yfinance) et simulation des donnees."""
import numpy as np
import pandas as pd


def get_ohlcv(ticker="AAPL", period="5y", retries=3):
    """Telecharge Open/High/Low/Close/Volume (cours ajustes) via yfinance, avec reessais."""
    import time
    import yfinance as yf
    last_error = None
    for _ in range(retries):
        try:
            df = yf.Ticker(ticker).history(period=period, auto_adjust=True)
            df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
            if not df.empty:
                return df
        except Exception as e:
            last_error = e
        time.sleep(2)
    raise ConnectionError(f"yfinance n'a renvoye aucune donnee ({last_error})")


def get_prices(ticker="AAPL", period="2y"):
    """Prix de cloture ajustes via yfinance."""
    return get_ohlcv(ticker, period)["Close"]


def log_returns(px: pd.Series) -> pd.Series:
    return np.log(px / px.shift(1)).dropna()


def historical_vol(px: pd.Series, trading_days=252) -> float:
    """Volatilite historique annualisee = ecart-type des rendements log * sqrt(252)."""
    return float(log_returns(px).std() * np.sqrt(trading_days))


if __name__ == "__main__":
    px = get_prices("AAPL", "2y")
    print(f"AAPL : {len(px)} jours, dernier cours = {float(px.iloc[-1]):.2f}")
    print(f"Volatilite historique annualisee = {historical_vol(px):.2%}")