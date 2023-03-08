from odoo.tests.common import SavepointCase
from odoo import fields
from datetime import timedelta


class PurchaseSellerEvaluation(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env.ref('product.product_product_2')

    def test_sale_order(self):
        crm_lead = self.env["crm.lead"].create({
            'name': "Lead",
        })

        sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_12').id,
            'date_order': fields.Date.today(),
            'expected_date': fields.Date.today() + timedelta(days=20),
            'opportunity_id': crm_lead.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 20,
                    'product_uom': self.product.uom_po_id.id,
                    'price_unit': self.product.list_price,
                    'name': self.product.name,
                }),
            ]
        })
        sale_order.action_confirm()
        self.assertEqual(
            len(sale_order.order_line), 1, msg="Order line was not created")
