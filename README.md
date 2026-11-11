# Projet 6 – Delta-Hedging & Gestion du Risque

Projet intégrateur du module **Finance des Marchés et ERP**
Cycle Ingénieur – Informatique Décisionnelle et IA, ENSA Safi (Université Cadi Ayyad)
Encadrant : Pr. Abdelilah JRAIFI – Année universitaire 2026-2027

## Membres du groupe 6

| Nom | Filière |
|---|---|
| ISSIMOR Khaoula | IDIA3 |
| KHEZAZ Leila | IDIA3 |
| KHAYATI Meryem | GINF3 |
| ER-REGUIGUE Halima | GINF3 |

## Sujet

Simuler la couverture dynamique (delta-hedging) d'une option vendue en rééquilibrant le Delta chaque jour, puis mesurer le P&L final de la stratégie. Le projet comprend :

- un moteur de calcul Python (Black-Scholes, Grecques, simulation GBM, couverture delta) ;
- une extension du module Odoo `cours_derives` : modèle `cours.hedging` et Wizard de simulation sur 30 jours ;
- un modèle d'IA (Random Forest) qui anticipe la volatilité du lendemain pour adapter la fréquence de couverture.

### Formules clés

- Delta : `Δ_k = N(d1(S_k, T - t_k))`
- Cash : `Cash_{k+1} = Cash_k · e^{rΔt} - (Δ_{k+1} - Δ_k) · S_{k+1}`
- P&L final : `Cash_n + Δ_n · S_n - payoff(S_n)`
- Le P&L moyen est proche de 0 ; sa dispersion mesure l'erreur de couverture (en 1/√n avec n le nombre de rééquilibrages).
- Gain de couverture : il dépend de l'écart entre la volatilité réalisée et la volatilité implicite (σ_pricing) utilisée pour le prix.

## Structure du dépôt

```
projet-groupe6/
├── README.md
├── pytest.ini               # configuration pytest (à la racine)
├── requirements.txt
├── docs/                    # fiche de lecture, Gantt, rapport
├── notebooks/               # prototypes (données, modèle Python, IA)
├── src/
│   ├── __init__.py
│   └── pricing.py           # fonctions financières pures (sans Odoo)
├── tests/
│   └── test_pricing.py      # tests pytest
├── odoo_addons/
│   └── cours_derives/       # module du TP 0 étendu (_inherit + cours.hedging)
└── docker-compose.yml       # Odoo 17 + PostgreSQL
```

## Contenu de `src/pricing.py`

| Fonction | Rôle |
|---|---|
| `bs_price(S, K, T, r, sigma, kind)` | Prix Black-Scholes d'une option européenne |
| `greeks(S, K, T, r, sigma, kind)` | Renvoie `{delta, gamma, vega, theta, rho}` |
| `payoff(ST, K, kind)` | Payoff à l'échéance |
| `simulate_gbm(S0, mu, sigma, T, n, n_paths, seed)` | Trajectoires GBM (schéma exact), tableau `(n_paths, n+1)` |
| `delta_hedge(S, K, T, r, sigma, kind)` | P&L final de la couverture sur une trajectoire |
| `delta_hedge_paths(S, K, T, r, sigma_pricing, kind, every)` | Couverture vectorisée sur M trajectoires, avec fréquence de rééquilibrage (`every` = 1 quotidien, 5 hebdomadaire, 21 mensuel) |

La volatilité réelle est celle utilisée pour simuler `S` ; elle peut différer de `sigma_pricing`.

## Installation

Prérequis : Python 3.10+, Git, Docker (pour la partie Odoo).

```bash
git clone https://github.com/Meryem-Khayati/projet-groupe6.git
cd projet-groupe6

# Environnement virtuel (recommandé)
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows PowerShell
# source venv/bin/activate          # Linux / macOS

pip install -r requirements.txt
```

> **Note** : `pytest` est fixé à la version `8.3.5` dans `requirements.txt`, car la version 9.2.0 provoque une erreur interne (`'NodeId' object has no attribute '_str_cache'`).

## Lancer le projet

### Démonstration rapide

```bash
python -m src.pricing
```

Affiche le prix du call, son Delta, ainsi que le P&L moyen et l'écart-type sur 1 000 trajectoires.

### Tests

```bash
python -m pytest
```

### Odoo (Docker)

```bash
docker compose up -d
```

Odoo est alors accessible sur `http://localhost:8069`. Installer ensuite le module `cours_derives` depuis Applications.

## Références

- Polycopié du cours, chapitre 6 (Delta-Hedging)
- Guide complet des projets intégrateurs, Projet 6
