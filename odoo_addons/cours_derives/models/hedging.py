
import numpy as np

from odoo import models, fields
from odoo.exceptions import UserError

from ..tools import simulate_gbm, delta_hedge_paths


class CoursHedging(models.Model):
    _name = "cours.hedging"
    _description = "Simulation de couverture Delta"

    name = fields.Char(string="Référence", required=True)

    option_id = fields.Many2one(
        "cours.option",
        string="Option concernée",
        required=True
    )

    quantity = fields.Float(
        string="Quantité d'options vendues",
        default=1.0
    )

    pricing_volatility = fields.Float(
        string="Volatilité de pricing"
    )

    realized_volatility = fields.Float(
        string="Volatilité réalisée"
    )

    hedge_frequency = fields.Selection(
        [
            ("daily", "Quotidienne"),
            ("weekly", "Hebdomadaire"),
            ("monthly", "Mensuelle"),
        ],
        string="Fréquence de couverture",
        default="daily",
        required=True
    )

    final_pnl = fields.Float(
        string="Profit / Perte final"
    )

    rebalance_count = fields.Integer(
        string="Nombre de rééquilibrages",
        default=0
    )

    def action_compute_hedging(self):
        for rec in self:
            option = rec.option_id

            if not option:
                raise UserError("Veuillez sélectionner une option.")

            if option.S0 <= 0 or option.K <= 0 or option.T <= 0:
                raise UserError(
                    "Le prix du sous-jacent, le strike et la maturité "
                    "doivent être positifs."
                )

            if rec.quantity <= 0:
                raise UserError("La quantité vendue doit être positive.")

            if rec.pricing_volatility <= 0 or rec.realized_volatility <= 0:
                raise UserError(
                    "Les deux volatilités doivent être strictement positives."
                )

            frequencies = {
                "daily": 1,
                "weekly": 5,
                "monthly": 21,
            }

            every = frequencies[rec.hedge_frequency]

            n_steps = 252
            n_paths = 1000
            mu = 0.05

            paths = simulate_gbm(
                S0=option.S0,
                mu=mu,
                sigma=rec.realized_volatility,
                T=option.T,
                n=n_steps,
                n_paths=n_paths,
                seed=42
            )

            pnl = delta_hedge_paths(
                S=paths,
                K=option.K,
                T=option.T,
                r=option.r,
                sigma_pricing=rec.pricing_volatility,
                kind=option.option_type,
                every=every
            )

            rec.final_pnl = float(np.mean(pnl)) * rec.quantity
            rec.rebalance_count = len(range(every, n_steps, every))
