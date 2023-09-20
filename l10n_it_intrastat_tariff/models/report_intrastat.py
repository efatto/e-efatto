# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ReportIntrastatCode(models.Model):
    _inherit = "report.intrastat.code"

    tariff_id = fields.Many2one(
        comodel_name="report.intrastat.tariff", string="Customs Tariff"
    )


class ReportIntrastatTariff(models.Model):
    _name = "report.intrastat.tariff"
    _description = "Customs Tariff"

    name = fields.Char()
    active = fields.Boolean(default=True)
    tariff_percentage = fields.Float()
