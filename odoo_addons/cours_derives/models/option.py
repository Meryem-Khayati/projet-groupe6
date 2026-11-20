
import math

from odoo import api, fields, models
from ..tools import bs_price, greeks


class OptionContract(models.Model):
    _name = "cours.option"
    _description = "Option vanille"

    name = fields.Char(string="Reference", required=True)

    option_type = fields.Selection(
        [
            ("call", "Call"),
            ("put", "Put"),
        ],
        string="Type",
        required=True,
        default="call"
    )

    # Parametres de l'option
    S0 = fields.Float(string="Prix actuel du sous-jacent")
    S_T = fields.Float(string="Sous-jacent a l'echeance")
    K = fields.Float(string="Strike")
    r = fields.Float(string="Taux sans risque")
    T = fields.Float(string="Maturite (annees)")
    sigma = fields.Float(string="Volatilite")

    # Prime calculee par Black-Scholes
    premium = fields.Float(
        string="Prime Black-Scholes",
        compute="_compute_black_scholes",
        store=True
    )

    # Grecques calculees automatiquement
    delta = fields.Float(
        string="Delta",
        compute="_compute_black_scholes",
        store=True
    )

    gamma = fields.Float(
        string="Gamma",
        compute="_compute_black_scholes",
        store=True
    )

    vega = fields.Float(
        string="Vega",
        compute="_compute_black_scholes",
        store=True
    )

    theta = fields.Float(
        string="Theta",
        compute="_compute_black_scholes",
        store=True
    )

    rho = fields.Float(
        string="Rho",
        compute="_compute_black_scholes",
        store=True
    )

    # Payoff et profit net
    payoff = fields.Float(
        string="Payoff",
        compute="_compute_payoff",
        store=True
    )

    profit = fields.Float(
        string="Profit net",
        compute="_compute_payoff",
        store=True
    )

    @api.depends("S0", "K", "T", "r", "sigma", "option_type")
    def _compute_black_scholes(self):
        for rec in self:
            if rec.S0 <= 0 or rec.K <= 0 or rec.T <= 0 or rec.sigma <= 0:
                rec.premium = 0.0
                rec.delta = 0.0
                rec.gamma = 0.0
                rec.vega = 0.0
                rec.theta = 0.0
                rec.rho = 0.0
                continue

            rec.premium = float(
                bs_price(
                    rec.S0,
                    rec.K,
                    rec.T,
                    rec.r,
                    rec.sigma,
                    rec.option_type
                )
            )

            values = greeks(
                rec.S0,
                rec.K,
                rec.T,
                rec.r,
                rec.sigma,
                rec.option_type
            )

            rec.delta = float(values["delta"])
            rec.gamma = float(values["gamma"])
            rec.vega = float(values["vega"])
            rec.theta = float(values["theta"])
            rec.rho = float(values["rho"])

    @api.depends("option_type", "S_T", "K", "premium")
    def _compute_payoff(self):
        for rec in self:
            if rec.option_type == "call":
                rec.payoff = max(rec.S_T - rec.K, 0.0)
            else:
                rec.payoff = max(rec.K - rec.S_T, 0.0)

            rec.profit = rec.payoff - rec.premium

    @api.model
    def put_par_parite(self, C, S0, K, r, T):
        return C - S0 + K * math.exp(-r * T)
