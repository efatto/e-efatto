# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ReportIntrastatCode(models.Model):
    _inherit = "report.intrastat.code"

    tariff_id = fields.Many2one(
        comodel_name="report.intrastat.tariff",
        string="Customs Tariff")


class ReportIntrastatTariff(models.Model):
    _name = "report.intrastat.tariff"
    _description = "Customs Tariff"

    name = fields.Char()
    active = fields.Boolean(default=True)
    tariff_percentage = fields.Float()
    currency_id = fields.Many2one(
        'res.currency',
        required=True,
        default=lambda self: self.env.user.company_id.currency_id.id,
        string="Currency",
    )
    tariff_fixed_value = fields.Monetary(
        currency_field='currency_id',
        default=0.0,
    )
