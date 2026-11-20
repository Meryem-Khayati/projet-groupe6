"""
src/ml.py - Features et Random Forest pour la prévision de volatilité
Groupe 6 : Delta-Hedging - rôle Ingénieur IA / Testeur
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error


def load_aapl(path="data/aapl.csv"):
    """Charge les prix AAPL (colonnes Open, High, Low, Close, Volume)."""
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df


def build_features(px, volume):
    """
    Construit le DataFrame de features + cible.
    - px     : Series des prix de clôture
    - volume : Series des volumes
    Retourne un DataFrame sans NaN, avec colonnes :
      ret, ret_lag1, vol_5, vol_10, vol_20, volume, target
    """
    df = pd.DataFrame({"ret": np.log(px / px.shift(1)), "volume": volume})
    df["ret_lag1"] = df["ret"].shift(1)
    for w in (5, 10, 20):
        df[f"vol_{w}"] = df["ret"].rolling(w).std() * np.sqrt(252)
    # Proxy de la vol réalisée de demain : |rendement de demain|
    df["target"] = df["ret"].abs().shift(-1)
    return df.dropna()


def split_chronologique(df, test_ratio=0.2):
    """Découpage chronologique (pas de shuffle). Retourne X_tr, X_te, y_tr, y_te."""
    X = df.drop(columns=["target"])
    y = df["target"]
    cut = int(len(df) * (1 - test_ratio))
    return X.iloc[:cut], X.iloc[cut:], y.iloc[:cut], y.iloc[cut:]


def train_random_forest(X_tr, y_tr, n_estimators=200, random_state=42):
    """Entraîne un RandomForestRegressor et le retourne."""
    rf = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state, n_jobs=-1)
    rf.fit(X_tr, y_tr)
    return rf


def evaluate(rf, X_te, y_te):
    """Retourne (rmse_rf, rmse_baseline) où baseline = vol_5 de la veille."""
    y_pred = rf.predict(X_te)
    rmse_rf = float(np.sqrt(mean_squared_error(y_te, y_pred)))
    rmse_baseline = float(np.sqrt(mean_squared_error(y_te, X_te["vol_5"])))
    return rmse_rf, rmse_baseline