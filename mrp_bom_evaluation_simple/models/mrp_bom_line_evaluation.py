# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class MrpBomLineEvaluation(models.Model):
    _inherit = 'mrp.bom.line'
    _name = 'mrp.bom.line.evaluation'

    bom_id = fields.Many2one(
        'mrp.bom.evaluation', 'Parent BoM',
        index=True, ondelete='cascade', required=True)
    price_unit = fields.Float(
        digits=dp.get_precision('Product Price'),
        groups='account.group_account_user')
    price_subtotal = fields.Float(
        compute='_compute_price_subtotal',
        compute_sudo=True,
        digits=dp.get_precision('Product Price'),
        groups='account.group_account_user',
        store=True)
    price_write_date = fields.Datetime(
        'Last price update')
    note = fields.Char()
    price_validated = fields.Boolean()

    @api.onchange('product_id')
    def onchange_product_id(self):
        # this onchange work only when an account user change the product
        res = super().onchange_product_id()
        if self.product_id:
            cost_histories = self.env["product.price.history"].search([
                ('product_id', '=', self.product_id.id),
                ('cost', '!=', 0.0),
            ], order='datetime desc')
            if cost_histories:
                self.price_write_date = cost_histories[0].datetime
            self.price_unit = self.product_id.standard_price
        return res

    @api.depends('product_id', 'price_unit', 'product_qty')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.price_unit * line.product_qty
