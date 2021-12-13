# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MrpBomPurchaseLink(models.TransientModel):
    _name = 'mrp.bom.purchase.link'
    _description = 'Link bom line to purchase order line'

    purchase_order_id = fields.Many2one(
        'purchase.order',
        domain=[('state', '!=', 'cancel')],
        required=True)

    @api.multi
    def action_done(self):
        self.ensure_one()
        bom = self.env['mrp.bom'].browse(
            self.env.context['active_id'])
        # get prices from purchase order for the matching products
        #  and save id of purchase.order.line
        for line in bom.bom_line_ids:
            if line.product_id in self.purchase_order_id.order_line.mapped(
                    'product_id'):
                purchase_order_line = self.purchase_order_id.order_line.filtered(
                    lambda x: x.product_id == line.product_id)[0]
                line.write(dict(
                    price_unit=purchase_order_line.price_unit,
                    purchase_order_line_id=purchase_order_line.id,
                    price_write_date=purchase_order_line.date_order,
                ))
        return {'type': 'ir.actions.act_window_close'}
