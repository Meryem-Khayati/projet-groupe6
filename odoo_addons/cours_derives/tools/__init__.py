import numpy as np
from scipy.stats import norm



# ---------------------------------------------------------------- Black-Scholes
def _d1_d2(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return d1, d1 - sigma * np.sqrt(T)


def bs_price(S, K, T, r, sigma, kind="call"):
    """Prix Black-Scholes d'une option europeenne."""
    d1, d2 = _d1_d2(S, K, T, r, sigma)
    if kind == "call":
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def greeks(S, K, T, r, sigma, kind="call"):
    """Renvoie {delta, gamma, vega, theta, rho}."""
    d1, d2 = _d1_d2(S, K, T, r, sigma)
    pdf = norm.pdf(d1)
    delta = norm.cdf(d1) if kind == "call" else norm.cdf(d1) - 1
    gamma = pdf / (S * sigma * np.sqrt(T))
    vega = S * pdf * np.sqrt(T)
    if kind == "call":
        theta = -S * pdf * sigma / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * norm.cdf(d2)
        rho = K * T * np.exp(-r * T) * norm.cdf(d2)
    else:
        theta = -S * pdf * sigma / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * norm.cdf(-d2)
        rho = -K * T * np.exp(-r * T) * norm.cdf(-d2)
    return {"delta": delta, "gamma": gamma, "vega": vega, "theta": theta, "rho": rho}




def simulate_gbm(S0, mu, sigma, T=1.0, n=252, n_paths=1, seed=42):
    """Simule des trajectoires de mouvement brownien géométrique."""
    rng = np.random.default_rng(seed)
    dt = T / n
    Z = rng.standard_normal((n_paths, n))
    log_ret = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z
    logS = np.log(S0) + np.concatenate(
        [np.zeros((n_paths, 1)), np.cumsum(log_ret, axis=1)],
        axis=1
    )
    return np.exp(logS)


def payoff(ST, K, kind="call"):
    return np.maximum(ST - K, 0.0) if kind == "call" else np.maximum(K - ST, 0.0)


def delta_hedge_paths(S, K, T, r, sigma_pricing, kind="call", every=1):
    """Calcule le P&L final sur plusieurs trajectoires."""
    M, n1 = S.shape
    n = n1 - 1
    dt = T / n
    premium = bs_price(S[0, 0], K, T, r, sigma_pricing, kind)
    delta = greeks(S[:, 0], K, T, r, sigma_pricing, kind)["delta"]
    cash = premium - delta * S[:, 0]
    last = 0

    for k in range(every, n, every):
        cash = cash * np.exp(r * (k - last) * dt)
        new_delta = greeks(
            S[:, k], K, T - k * dt, r, sigma_pricing, kind
        )["delta"]
        cash = cash - (new_delta - delta) * S[:, k]
        delta = new_delta
        last = k

    cash = cash * np.exp(r * (n - last) * dt)
    return cash + delta * S[:, -1] - payoff(S[:, -1], K, kind)
