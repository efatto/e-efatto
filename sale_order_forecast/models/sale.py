# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _bom_explode(self, product_id, products):
        bom = self.env['mrp.bom']._bom_find(
            product=product_id, company_id=self.company_id.id)
        if bom:
            bom_line_data = bom.explode(product_id, 1)[1]
            products.extend({
                'product_id': r[0].product_id.id,
                'qty': r[1]['qty'],
                'parent_id': product_id.id}
                for r in bom_line_data
            )
            for product in [
                r[0].product_id for r in bom_line_data
            ]:
                products = self._bom_explode(product, products)
        return products

    def open_report_stock_forecast(self):
        products = [x.id for x in self.mapped('order_line.product_id').filtered(
            lambda x: x.type != 'service'
        )]
        # get all products from bom and its children
        child_products = []
        for line in self.order_line:
            child_products = self._bom_explode(line.product_id, child_products)
        if child_products:
            child_products = list(set([x['product_id'] for x in child_products]))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Report stock forecast for product and components',
            'view_mode': 'pivot,graph',
            'domain': ['|',
                       ('product_id', 'in', products),
                       ('child_product_id', 'in', child_products)],
            'res_model': 'report.stock.sale.forecast',
            'target': 'current',
            'context': {},
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def open_report_stock_forecast_line(self):
        product = self.product_id.id if self.product_id.type != 'service' else False
        if product:
            domain = [('product_id', '=', product)]
            # get all products from bom and its children
            child_products = self.order_id._bom_explode(self.product_id, [])
            if child_products:
                child_products = list(set([x['product_id'] for x in child_products]))
            view = self.env.ref(
                'sale_order_forecast.view_stock_sale_forecast_pivot_component')
            if child_products:
                domain = [
                    '|',
                    ('product_id', '=', product),
                    ('child_product_id', 'in', child_products)
                ]
            return {
                'type': 'ir.actions.act_window',
                'name': 'Report stock forecast for product and components',
                'view_mode': 'pivot',
                'domain': domain,
                'view_id': view.id,
                'res_model': 'report.stock.sale.forecast',
                'target': 'new',
                'context': {},
            }
