# © 2015-2016 Akretion (http://www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# @author Raphaël Valyi <rvalyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    price_history_ids = fields.One2many(
        comodel_name='product.price.history',
        inverse_name='product_id',
        string='Product Price History')

    def show_product_price_history(self):
        self.ensure_one()
        action = self.env.ref(
            'product_cost_history.product_price_history_action').read()[0]
        action['domain'] = [('product_id', '=', self.id)]
        return action
