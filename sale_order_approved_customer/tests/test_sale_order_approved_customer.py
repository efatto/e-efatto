# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import SavepointCase


class TestSaleDeliveryRecreate(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref('base.res_partner_2')
        cls.product1 = cls.env.ref('product.product_product_25')
        cls.product1.invoice_policy = 'order'

    def _create_sale_order_line(self, order, product, qty):
        line = self.env['sale.order.line'].create([{
            'order_id': order.id,
            'product_id': product.id,
            'product_uom_qty': qty,
            'price_unit': 100,
        }])
        line.product_id_change()
        line._convert_to_write(line._cache)
        return line

    def test_01_sale_approved(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self._create_sale_order_line(order, self.product1, 5)
        order.with_context(test_sale_order_approved_customer=True).action_confirm()
        self.assertEqual(order.state, 'approved')
        order.with_context(test_sale_order_approved_customer=True).action_confirm()
        self.assertEqual(order.state, 'sale')
        order.action_cancel()
        self.assertEqual(order.state, 'cancel')
