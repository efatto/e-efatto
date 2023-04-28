# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData
from odoo.tools import mute_logger


class TestPurchaseSaleMrpSearch(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env.ref('base.res_partner_3')
        supplierinfo = cls.env['product.supplierinfo'].create({
            'name': cls.vendor.id,
        })
        cls.partner = cls.env.ref('base.res_partner_2')
        cls.partner.customer = True
        cls.product_bom_purchase = cls.env['product.product'].create([{
            'name': 'Component product to purchase',
            'default_code': 'BOM1234',
            'type': 'product',
            'purchase_ok': True,
            'route_ids': [
                (4, cls.env.ref('purchase_stock.route_warehouse0_buy').id),
                (4, cls.env.ref('stock.route_warehouse0_mto').id)],
            'seller_ids': [(6, 0, [supplierinfo.id])],
        }])
        cls.main_bom.write({
            'bom_line_ids': [
                (0, 0, {
                    'product_id': cls.product_bom_purchase.id,
                    'product_qty': 10,
                    'product_uom_id': cls.product_bom_purchase.uom_id.id,
                })
            ]
        })

    def _create_sale_order_line(self, order, product, qty):
        vals = {
            'order_id': order.id,
            'product_id': product.id,
            'product_uom_qty': qty,
            'price_unit': 100,
            }
        line = self.env['sale.order.line'].create(vals)
        line.product_id_change()
        line._convert_to_write(line._cache)
        return line

    def test_purchase_mrp_sale_origin(self):
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self._create_sale_order_line(order1, self.top_product, 3)
        self._create_sale_order_line(order1, self.product_bom_purchase, 5)
        order1.action_confirm()
        self.assertEqual(order1.state, 'sale')
        with mute_logger('odoo.addons.stock.models.procurement'):
            self.procurement_model.run_scheduler()
        self.production = self.env['mrp.production'].search(
            [('origin', '=', order1.name)])
        self.assertTrue(self.production)
        self.production.action_assign()
        with mute_logger('odoo.addons.stock.models.procurement'):
            self.procurement_model.run_scheduler()
        purchase_orders = self.env['purchase.order'].search([
            ('partner_id', '=', self.vendor.id),
            ('order_line.product_id', 'in', [self.product_bom_purchase.id]),
        ])
        # fixme in origin only 1 purchase order was found, which module forced two?
        self.assertTrue(purchase_orders)
        self.assertIn(self.production.origin, purchase_orders.mapped('mrp_origin'))
