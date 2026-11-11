
import math

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ForwardContract(models.Model):
    _name = "cours.forward"
    _description = "Contrat forward"

    # Seuil de tolerance pour la detection d'arbitrage
    TOL = 0.01

    # Informations du contrat
    name = fields.Char(string="Reference", required=True)
    S0 = fields.Float(string="Prix spot", required=True)
    r = fields.Float(string="Taux sans risque (decimal)", required=True)
    T = fields.Float(string="Maturite (ans)", required=True)

    # Prix forward theorique
    F0 = fields.Float(
        string="Prix forward",
        digits=(16, 4),
        compute="_compute_F0",
        store=True,
        readonly=False,
    )

    # Exercice A : valeur du forward en cours de vie
    t_elapsed = fields.Float(string="Temps ecoule (ans)")
    S_t = fields.Float(string="Prix spot courant")

    value = fields.Float(
        string="Valeur du forward",
        compute="_compute_value",
        store=True,
    )

    # Exercice B : detection d'arbitrage
    market_price = fields.Float(
        string="Prix cote",
        digits=(16, 4),
    )

    arbitrage_gain = fields.Float(
        string="Gain d'arbitrage",
        compute="_compute_arbitrage_gain",
        store=True,
    )

    strategy = fields.Selection(
        [
            ("sell", "Vendre le forward"),
            ("buy", "Acheter le forward"),
            ("none", "Aucun arbitrage"),
        ],
        string="Strategie",
        compute="_compute_strategy",
        store=True,
    )

    # Calcul du prix forward theorique
    @api.depends("S0", "r", "T")
    def _compute_F0(self):
        for rec in self:
            rec.F0 = rec.S0 * math.exp(rec.r * rec.T)

    # Calcul de la valeur du forward en cours de vie
    @api.depends("S_t", "F0", "r", "T", "t_elapsed")
    def _compute_value(self):
        for rec in self:
            rec.value = (
                rec.S_t
                - rec.F0 * math.exp(-rec.r * (rec.T - rec.t_elapsed))
            )

    # Calcul du gain d'arbitrage
    @api.depends("market_price", "F0")
    def _compute_arbitrage_gain(self):
        for rec in self:
            if not rec.market_price:
                rec.arbitrage_gain = 0.0
            else:
                rec.arbitrage_gain = rec.market_price - rec.F0

    # Determination de la strategie d'arbitrage
    @api.depends("arbitrage_gain")
    def _compute_strategy(self):
        for rec in self:
            if rec.arbitrage_gain > self.TOL:
                rec.strategy = "sell"
            elif rec.arbitrage_gain < -self.TOL:
                rec.strategy = "buy"
            else:
                rec.strategy = "none"

    # Verification du temps ecoule
    @api.constrains("t_elapsed", "T")
    def _check_t_elapsed(self):
        for rec in self:
            if rec.t_elapsed < 0 or rec.t_elapsed > rec.T:
                raise ValidationError(
                    "Le temps ecoule doit etre compris entre 0 et la maturite T."
                )
