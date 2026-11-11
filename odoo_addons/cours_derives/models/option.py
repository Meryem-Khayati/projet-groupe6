import math
from odoo import api, fields, models



class OptionContract(models.Model):
    _name = "cours.option"
    _description = "Option vanille"

    name = fields.Char(string="Reference", required=True)

    option_type = fields.Selection(
        [("call", "Call"), ("put", "Put")],
        string="Type",
        required=True,
        default="call"
    )

    S_T = fields.Float(string="Sous-jacent a l'echeance")
    K = fields.Float(string="Strike")
    premium = fields.Float(string="Prime")

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
