# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_stock_deposit_id = fields.Many2one(
        'stock.location', string="Deposit Location",
        company_dependent=True,
        help="The stock location used as source when sending goods to this contact "
             "using a rule with `use_partner_stock_deposit` enabled."
    )