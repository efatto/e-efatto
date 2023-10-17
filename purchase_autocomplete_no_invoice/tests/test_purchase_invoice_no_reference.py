# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests.common import Form, SavepointCase


class PurchaseInvoiceNoReference(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.user_model = cls.env["res.users"].with_context(no_reset_password=True)
        cls.vendor = cls.env.ref("base.res_partner_3")
        cls.product = cls.env.ref("product.product_product_1")

    def test_purchase_order(self):
        purchase_form = Form(self.env["purchase.order"])
        purchase_form.date_order = fields.Date.today()
        purchase_form.partner_id = self.vendor
        purchase_form.partner_ref = "Vendor Reference"
        with purchase_form.order_line.new() as purchase_line_form:
            purchase_line_form.product_id = self.product
            purchase_line_form.product_qty = 20
            purchase_line_form.product_uom = self.product.uom_po_id
            purchase_line_form.price_unit = self.product.list_price
            purchase_line_form.name = self.product.name
            purchase_line_form.date_planned = fields.Date.today() + timedelta(days=20)
        purchase_order = purchase_form.save()
        purchase_order.button_confirm()
        self.assertEqual(
            len(purchase_order.order_line), 1, msg="Order line was not created"
        )
        invoice_form = Form(
            self.env["account.move"].with_context(
                check_move_validity=False,
                company_id=self.env.user.company_id.id,
                default_move_type="in_invoice",
            )
        )
        invoice_form.date = fields.Date.today()
        invoice_form.partner_id = self.vendor
        invoice_form.ref = "Invoice Reference"
        invoice = invoice_form.save()
        vendor_bill_purchase_id = self.env["purchase.bill.union"].search(
            [("reference", "=", "Vendor Reference")]
        )
        self.assertTrue(vendor_bill_purchase_id)
        invoice.purchase_vendor_bill_id = vendor_bill_purchase_id
        self.assertEqual(invoice.ref, "Invoice Reference")
