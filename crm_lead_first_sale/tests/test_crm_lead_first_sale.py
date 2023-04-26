from odoo.tests.common import SavepointCase
from odoo import fields
from datetime import timedelta


class PurchaseSellerEvaluation(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env.ref('product.product_product_2')

    def test_00_sale_order_send(self):
        crm_lead = self.env["crm.lead"].create({
            'name': "Lead",
            'create_date': fields.Date.today() + timedelta(days=-12),
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
        self.assertEqual(
            len(sale_order.order_line), 1, msg="Order line was not created")
        self.assertEqual(crm_lead.first_sale_days, 0)

        sale_order.force_quotation_send()
        message_ids = sale_order.message_ids.filtered(
            lambda x: x.subject and 'Quotation' in x.subject)
        self.assertEqual(len(message_ids), 1)
        message_id = message_ids[0]
        message_id.date = message_id.date + timedelta(days=-3)
        self.assertEqual(crm_lead.first_sale_days, 9)

        sale_order.action_confirm()
        self.assertEqual(crm_lead.first_sale_days, 9)

    def test_01_sale_order_confirm(self):
        crm_lead = self.env["crm.lead"].create({
            'name': "Lead",
            'create_date': fields.Date.today() + timedelta(days=-7),
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
        self.assertEqual(
            len(sale_order.order_line), 1, msg="Order line was not created")
        self.assertEqual(crm_lead.first_sale_days, 0)

        sale_order.action_confirm()
        self.assertEqual(crm_lead.first_sale_days, 7)

        sale_order.force_quotation_send()
        message_ids = sale_order.message_ids.filtered(
            lambda x: x.subject and 'Order' in x.subject)
        self.assertEqual(len(message_ids), 1)
        message_id = message_ids[0]
        message_id.date = message_id.date + timedelta(days=-3)
        self.assertEqual(crm_lead.first_sale_days, 7)
