# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase
from odoo import fields
from datetime import timedelta


class PurchaseInvoiceNoReference(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env.ref('base.res_partner_3')
        cls.product = cls.env.ref('product.product_product_1')

    def test_purchase_order(self):
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'date_order': fields.Date.today(),
            'partner_ref': 'Vendor Reference',
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_qty': 20,
                    'product_uom': self.product.uom_po_id.id,
                    'price_unit': self.product.list_price,
                    'name': self.product.name,
                    'date_planned': fields.Date.today() + timedelta(days=20),
                }),
            ]
        })
        purchase_order.button_confirm()
        self.assertEqual(
            len(purchase_order.order_line), 1, msg="Order line was not created")
        account_invoice = self.env['account.invoice'].create({
            'partner_id': self.vendor.id,
            'date': fields.Date.today(),
            'reference': 'Invoice Reference',
        })
        vendor_bill_purchase_id = self.env['purchase.bill.union'].search([
            ('reference', '=', 'Vendor Reference')
        ])
        self.assertTrue(vendor_bill_purchase_id)
        account_invoice.vendor_bill_purchase_id = vendor_bill_purchase_id
        self.assertEqual(account_invoice.reference, 'Invoice Reference')
