
from odoo import models, fields


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
