from datetime import timedelta

from odoo import fields
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class PurchaseInvoiceNoReference(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env.ref("base.res_partner_3")
        cls.product = cls.env.ref("product.product_product_1")
        cls.purchase_journal = cls.company_data["default_journal_purchase"]

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
        invoice = self._create_invoice(
            move_type="in_invoice",
            journal_id=self.purchase_journal,
            partner_id=self.vendor,
            ref="Invoice Reference",
            post=False,
            invoice_line_ids=[
                self._prepare_invoice_line(
                    product_id=self.env.ref("product.product_product_5"),
                    quantity=5.0,
                    price_unit=6,
                    discount=10,
                )
            ],
        )
        invoice.action_post()
        vendor_bill_purchase_id = self.env["purchase.bill.union"].search(
            [("reference", "=", "Vendor Reference")]
        )
        self.assertTrue(vendor_bill_purchase_id)
        invoice.purchase_vendor_bill_id = vendor_bill_purchase_id
        self.assertEqual(invoice.ref, "Invoice Reference")
