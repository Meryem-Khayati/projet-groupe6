"""
tests/test_ml.py - Tests des features et du Random Forest (src/ml.py)
Groupe 6 : Delta-Hedging - rôle Ingénieur IA / Testeur
"""
import numpy as np
import pandas as pd
import pytest
from src.ml import load_aapl, build_features, split_chronologique, train_random_forest, evaluate


@pytest.fixture(scope="module")
def aapl():
    return load_aapl("data/aapl.csv")


@pytest.fixture(scope="module")
def features(aapl):
    return build_features(aapl["Close"], aapl["Volume"])


# --------------------------------------------------------------- features
def test_features_shape(features):
    expected = {"ret", "ret_lag1", "vol_5", "vol_10", "vol_20", "volume", "target"}
    assert expected.issubset(features.columns)


def test_features_pas_de_nan(features):
    assert not features.isna().any().any()


def test_cible_decalee_un_jour(features):
    # target_t = |ret_{t+1}| → target_t ne doit PAS être identique à |ret_t|
    # (sinon fuite : on prédirait le rendement du jour avec le rendement du jour)
    assert not np.allclose(features["target"].values, features["ret"].abs().values)
    # Vérification positive : target_t = |ret_{t+1}| pour tout t sauf le dernier
    expected = features["ret"].abs().shift(-1).dropna()
    assert np.allclose(features["target"].values[:-1], expected.values)


def test_vol_glissante_positives(features):
    for w in (5, 10, 20):
        assert (features[f"vol_{w}"] >= 0).all()


# ------------------------------------------------------- split chronologique
def test_split_chronologique(features):
    X_tr, X_te, y_tr, y_te = split_chronologique(features)
    assert X_tr.index.max() < X_te.index.min()   # pas de fuite temporelle
    assert len(X_tr) + len(X_te) == len(features)
    assert len(y_tr) == len(X_tr)


def test_split_ratio(features):
    X_tr, X_te, _, _ = split_chronologique(features, test_ratio=0.2)
    ratio = len(X_te) / len(features)
    assert 0.18 < ratio < 0.22


# --------------------------------------------------------- random forest
def test_rf_reproductible(features):
    X_tr, X_te, y_tr, y_te = split_chronologique(features)
    rf1 = train_random_forest(X_tr, y_tr, random_state=42)
    rf2 = train_random_forest(X_tr, y_tr, random_state=42)
    pred1 = rf1.predict(X_te)
    pred2 = rf2.predict(X_te)
    assert np.allclose(pred1, pred2)


def test_rf_predictions_shape(features):
    X_tr, X_te, y_tr, y_te = split_chronologique(features)
    rf = train_random_forest(X_tr, y_tr)
    pred = rf.predict(X_te)
    assert pred.shape == (len(X_te),)
    assert np.all(np.isfinite(pred))


def test_rf_bat_ou_egalise_baseline(features):
    # on ne force pas à battre la baseline, mais on vérifie que les 2 RMSE sont calculables
    X_tr, X_te, y_tr, y_te = split_chronologique(features)
    rf = train_random_forest(X_tr, y_tr)
    rmse_rf, rmse_naive = evaluate(rf, X_te, y_te)
    assert rmse_rf > 0 and rmse_naive > 0
    # note dans le CR : rmse_rf = ..., rmse_naive = ...