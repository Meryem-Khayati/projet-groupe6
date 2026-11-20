import numpy as np
from src.pricing import bs_price, greeks, simulate_gbm, delta_hedge, delta_hedge_paths

S, K, T, r, sigma = 100.0, 100.0, 1.0, 0.03, 0.20


def test_delta_finite_difference():
    h = 1e-3
    num = (bs_price(S + h, K, T, r, sigma) - bs_price(S - h, K, T, r, sigma)) / (2 * h)
    assert abs(num - greeks(S, K, T, r, sigma)["delta"]) < 1e-4


def test_gbm_shape_and_start():
    paths = simulate_gbm(S, 0.05, sigma, T, n=252, n_paths=50)
    assert paths.shape == (50, 253)
    assert np.allclose(paths[:, 0], S)


def test_hedge_single_path_matches_vectorized():
    paths = simulate_gbm(S, 0.05, sigma, T, n=252, n_paths=5, seed=1)
    vect = delta_hedge_paths(paths, K, T, r, sigma)
    for i in range(5):
        assert abs(delta_hedge(paths[i], K, T, r, sigma) - vect[i]) < 1e-8


def test_hedge_pnl_centered_near_zero():
    paths = simulate_gbm(S, 0.05, sigma, T, n=252, n_paths=2000)
    pnl = delta_hedge_paths(paths, K, T, r, sigma)
    assert abs(pnl.mean()) < 0.3
    assert pnl.std() < 2.0


def test_more_rebalancing_less_risk():
    paths = simulate_gbm(S, 0.05, sigma, T, n=252, n_paths=2000)
    daily = delta_hedge_paths(paths, K, T, r, sigma, every=1).std()
    monthly = delta_hedge_paths(paths, K, T, r, sigma, every=21).std()
    assert daily < monthly