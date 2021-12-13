# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    price_unit = fields.Float(
        digits=dp.get_precision('Product Price'),
        groups='account.group_account_user')
    price_subtotal = fields.Float(
        compute='_compute_price_subtotal',
        compute_sudo=True,
        digits=dp.get_precision('Product Price'),
        groups='account.group_account_user',
        store=True)
    weight_total = fields.Float(
        'Total Weight',
        digits=dp.get_precision('Stock Weight'),
        compute='_compute_weight_total',
        store=True)
    price_write_date = fields.Datetime(
        'Last price update',
        store=True)
    purchase_order_line_id = fields.Many2one(
        'purchase.order.line',
        string='Linked RDP/PO line')

    @api.depends('product_id', 'product_id.weight', 'product_qty')
    def _compute_weight_total(self):
        for line in self:
            line.weight_total = line.product_id.weight * line.product_qty

    @api.onchange('product_id')
    def onchange_product_id(self):
        # this onchange work only when an account user change the product
        res = super().onchange_product_id()
        purchase_order_line_ids = self.env['purchase.order.line'].search([
            ('product_id', '=', self.product_id.id),
            ('state', '!=', 'cancel'),
        ])
        price_unit = self.product_id.standard_price
        price_write_date = fields.Datetime.now()
        if purchase_order_line_ids:
            purchase_order_line_id = purchase_order_line_ids.sorted(
                'date_order', reverse=True
            )[0]
            if purchase_order_line_id.price_unit != 0.0:
                price_unit = purchase_order_line_id._get_discounted_price_unit()
                price_write_date = purchase_order_line_id.date_order
                if purchase_order_line_id.product_uom != self.product_uom_id:
                    price_unit = purchase_order_line_id.product_uom._compute_price(
                        price_unit, self.product_uom_id
                    )
                if purchase_order_line_id.currency_id != \
                        self.bom_id.company_id.currency_id:
                    price_unit = purchase_order_line_id.currency_id._convert(
                        price_unit,
                        self.bom_id.company_id.currency_id,
                        self.bom_id.company_id,
                        fields.Date.today(),
                    )
        self.price_unit = price_unit
        self.price_write_date = price_write_date
        return res

    @api.depends('product_id', 'price_unit', 'product_qty')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.price_unit * line.product_qty
