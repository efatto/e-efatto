# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_stock_deposit = fields.Many2one(
        'stock.location', string="Deposit Location",
        company_dependent=True,
        help="The stock location used as source when sending goods to this contact "
             "using a rule with `use_partner_stock_deposit` enabled."
    )

    def open_stock_deposit(self):
        domain = [('location_id', 'child_of', self.property_stock_deposit.id),
                  ('quantity', '!=', 0)]
        view = self.env.ref(
            'stock.view_stock_quant_tree')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock deposit',
            'domain': domain,
            'views': [(view.id, 'tree')],
            'res_model': 'stock.quant',
            'context': {'search_default_productgroup': 0},
        }
