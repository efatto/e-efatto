# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PurchaseSaleMrpUnlinkWizard(models.TransientModel):
    _name = 'purchase.sale.mrp.unlink.wizard'
    _description = 'Unlink all Sale Offers from this vendor RdP'

    purchase_order_id = fields.Many2one(
        'purchase.order', string='Purchase Order', required=True)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'purchase_order_id' in fields and not res.get('purchase_order_id')\
            and self._context.get('active_model') == 'purchase.order'\
                and self._context.get('active_id'):
            res['purchase_order_id'] = self._context['active_id']
        return res

    @api.multi
    def action_done(self):
        for wizard in self:
            purchase_order = wizard.purchase_order_id
            linked_sale_order_line_ids = self.env['sale.order.line'].search([
                ('purchase_line_id', 'in', purchase_order.order_line.ids)
            ])
            linked_sale_order_line_ids.write({
                'purchase_line_id': False,
            })
            linked_bom_line_ids = self.env['mrp.bom.line'].search([
                ('purchase_order_line_id', 'in', purchase_order.order_line.ids)
            ])
            linked_bom_line_ids.write({
                'purchase_order_line_id': False,
            })
        return {}
