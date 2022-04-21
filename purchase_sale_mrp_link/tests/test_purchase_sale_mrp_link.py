# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import SavepointCase
from odoo import fields


class TestPurchaseSaleMrpLink(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.user_model = cls.env['res.users'].with_context(no_reset_password=True)
        cls.vendor = cls.env.ref('base.res_partner_3')
        cls.partner = cls.env.ref('base.res_partner_2')
        cls.partner.customer = True
        cls.product = cls.env.ref('product.product_delivery_01')
        cls.product1 = cls.env.ref('product.product_delivery_02')

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

    def _create_purchase_order_line(self, order, product, qty):
        vals = {
            'order_id': order.id,
            'product_id': product.id,
            'product_qty': qty,
            'product_uom': product.uom_po_id.id,
            'price_unit': product.list_price,
            'name': product.name,
            'date_planned': fields.Date.today(),
        }
        line = self.env['purchase.order.line'].create(vals)
        line.onchange_product_id()
        line._convert_to_write(line._cache)
        return line

    def test_sale_link_product_simple(self):
        lead = self.env['crm.lead'].create([{
            'name': 'test',
            'lead_line_ids': [
                (0, 0, {'name': 'test line', 'product_id': self.product.id}),
            ]
        }])
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'opportunity_id': lead.id,
        })
        self._create_sale_order_line(sale_order, self.product, 5.0)
        self._create_sale_order_line(sale_order, self.product, 5.0)
        self._create_sale_order_line(sale_order, self.product1, 5.0)
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id
        })
        self._create_purchase_order_line(purchase_order, self.product, 5.0)
        self._create_purchase_order_line(purchase_order, self.product, 5.0)
        purchase_order.order_line[0]._onchange_quantity()
        self.assertEqual(
            len(purchase_order.order_line), 2, msg="Order line was not created")
        purchase_order.lead_line_id = lead.lead_line_ids[0]
        self.assertEqual(
            purchase_order.sale_order_ids.ids, sale_order.ids
        )
        # test unlink
        purchase_order.lead_line_id = False
        self.assertFalse(purchase_order.sale_order_ids)
