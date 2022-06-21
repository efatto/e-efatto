# © 2015-2016 Akretion (http://www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# @author Raphaël Valyi <rvalyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def show_product_price_history(self):
        self.ensure_one()
        products = self.env['product.product'].search(
            [('product_tmpl_id', '=', self._context['active_id'])])
        action = self.env.ref(
            'product_cost_history.product_price_history_action').read()[0]
        action['domain'] = [('product_id', 'in', products.ids)]
        return action
