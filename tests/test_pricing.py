import numpy as np
from src.pricing import bs_price


def test_parite_call_put():
    S, K, T, r, sigma = 100, 100, 1.0, 0.03, 0.2
    call = bs_price(S, K, T, r, sigma, "call")
    put = bs_price(S, K, T, r, sigma, "put")
    assert np.isclose(call - put, S - K * np.exp(-r * T))