"""
pricing.py - Fonctions financieres pures (sans Odoo)
Groupe 6 : Delta-Hedging & Gestion du Risque (Chap. 6)

Contenu :
  - bs_price / greeks : Black-Scholes (repris du Projet 1)
  - simulate_gbm      : simulation de trajectoires (mouvement brownien geometrique)
  - delta_hedge       : couverture delta d'UNE trajectoire (version du polycopie)
  - delta_hedge_paths : couverture delta vectorisee sur M trajectoires,
                        avec frequence de rebalancement et sigma_reelle != sigma_pricing
"""
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


def payoff(ST, K, kind="call"):
    return np.maximum(ST - K, 0.0) if kind == "call" else np.maximum(K - ST, 0.0)


# ------------------------------------------------------------------- Simulation
def simulate_gbm(S0, mu, sigma, T=1.0, n=252, n_paths=1, seed=42):
    """
    Simule n_paths trajectoires GBM (schema exact), tableau (n_paths, n+1).
    S_{t+dt} = S_t * exp((mu - sigma^2/2) dt + sigma sqrt(dt) Z)
    """
    rng = np.random.default_rng(seed)
    dt = T / n
    Z = rng.standard_normal((n_paths, n))
    log_ret = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z
    logS = np.log(S0) + np.concatenate([np.zeros((n_paths, 1)), np.cumsum(log_ret, axis=1)], axis=1)
    return np.exp(logS)


# -------------------------------------------------------------------- Couverture
def delta_hedge(S, K, T, r, sigma, kind="call"):
    """
    S : trajectoire (n+1 points). Vendeur d'une option, couverture quotidienne.
    Renvoie le P&L final (valeur a la maturite T).
    """
    n = len(S) - 1
    dt = T / n
    premium = bs_price(S[0], K, T, r, sigma, kind)
    delta = greeks(S[0], K, T, r, sigma, kind)["delta"]
    cash = premium - delta * S[0]          # on encaisse la prime, on achete delta actions
    for k in range(1, n):
        cash *= np.exp(r * dt)
        new_delta = greeks(S[k], K, T - k * dt, r, sigma, kind)["delta"]
        cash -= (new_delta - delta) * S[k]
        delta = new_delta
    cash *= np.exp(r * dt)
    return cash + delta * S[-1] - payoff(S[-1], K, kind)


def delta_hedge_paths(S, K, T, r, sigma_pricing, kind="call", every=1):
    """
    Version vectorisee : S de forme (M, n+1). Renvoie un vecteur de M P&L finaux.
    sigma_pricing : vol utilisee pour le prix et le delta (celle du trader).
    every         : rebalancement tous les 'every' pas (1 = quotidien, 5 = hebdo, 21 = mensuel).
    La vol reelle est celle qui a servi a simuler S (donc sigma_reelle != sigma_pricing possible).
    """
    M, n1 = S.shape
    n = n1 - 1
    dt = T / n
    premium = bs_price(S[0, 0], K, T, r, sigma_pricing, kind)
    delta = greeks(S[:, 0], K, T, r, sigma_pricing, kind)["delta"]
    cash = premium - delta * S[:, 0]
    last = 0
    for k in range(every, n, every):
        cash = cash * np.exp(r * (k - last) * dt)
        new_delta = greeks(S[:, k], K, T - k * dt, r, sigma_pricing, kind)["delta"]
        cash = cash - (new_delta - delta) * S[:, k]
        delta = new_delta
        last = k
    cash = cash * np.exp(r * (n - last) * dt)
    return cash + delta * S[:, -1] - payoff(S[:, -1], K, kind)


if __name__ == "__main__":
    S0, K, T, r, sigma = 100.0, 100.0, 1.0, 0.03, 0.20
    print("Call BS :", round(bs_price(S0, K, T, r, sigma, "call"), 4))
    print("Delta   :", round(greeks(S0, K, T, r, sigma)["delta"], 4))
    S = simulate_gbm(S0, mu=0.05, sigma=sigma, T=T, n=252, n_paths=1000)
    pnl = delta_hedge_paths(S, K, T, r, sigma)
    print(f"P&L moyen = {pnl.mean():.4f} | ecart-type = {pnl.std():.4f} (1000 trajectoires, couverture quotidienne)")