from datetime import timedelta

from odoo import fields
from odoo.tests.common import Form, SavepointCase


class PurchaseAutocompleteQtyToInvoice(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.user_model = cls.env["res.users"].with_context(no_reset_password=True)
        cls.vendor = cls.env.ref("base.res_partner_3")
        cls.product = cls.env.ref("product.product_delivery_01")
        cls.product2 = cls.env.ref("product.product_delivery_02")

    def test_00_purchase_order(self):
        purchase_form = Form(self.env["purchase.order"])
        purchase_form.date_order = fields.Date.today()
        purchase_form.partner_id = self.vendor
        purchase_form.partner_ref = "Vendor Reference ATCPO"
        with purchase_form.order_line.new() as purchase_line_form:
            purchase_line_form.product_id = self.product
            purchase_line_form.product_qty = 20
            purchase_line_form.product_uom = self.product.uom_po_id
            purchase_line_form.price_unit = self.product.list_price
            purchase_line_form.name = self.product.name
            purchase_line_form.date_planned = fields.Date.today() + timedelta(days=20)
        with purchase_form.order_line.new() as purchase_line_form:
            purchase_line_form.product_id = self.product2
            purchase_line_form.product_qty = 25
            purchase_line_form.product_uom = self.product2.uom_po_id
            purchase_line_form.price_unit = self.product2.list_price
            purchase_line_form.name = self.product2.name
            purchase_line_form.date_planned = fields.Date.today() + timedelta(days=20)
        purchase_order = purchase_form.save()
        purchase_order.button_confirm()
        self.assertEqual(
            len(purchase_order.order_line), 2, msg="Order line was not created"
        )
        picking = purchase_order.picking_ids
        # set done 10 pc of product
        for sml in picking.move_lines.mapped("move_line_ids").filtered(
            lambda x: x.product_id == self.product
        ):
            sml.qty_done = 10
        res = picking.button_validate()
        Form(self.env[res["res_model"]].with_context(res["context"])).save().process()
        backorder_picking = purchase_order.picking_ids - picking
        self.assertTrue(backorder_picking)
        invoice_form = Form(
            self.env["account.move"].with_context(
                check_move_validity=False,
                company_id=self.env.user.company_id.id,
                default_move_type="in_invoice",
            )
        )
        invoice_form.invoice_date = fields.Date.today()
        invoice_form.partner_id = self.vendor
        invoice_form.ref = "Invoice Reference"
        invoice = invoice_form.save()
        # purchase.bill.union is created only when at least one vendor invoice exists
        vendor_bill_purchase_id = self.env["purchase.bill.union"].search(
            [("reference", "=", "Vendor Reference ATCPO")]
        )
        self.assertTrue(vendor_bill_purchase_id)
        invoice_form1 = Form(
            self.env["account.move"]
            .with_context(
                check_move_validity=False,
                company_id=self.env.user.company_id.id,
            )
            .browse(invoice.id)
        )
        invoice_form1.purchase_vendor_bill_id = vendor_bill_purchase_id
        invoice1 = invoice_form1.save()
        self.assertEqual(invoice1.ref, "Invoice Reference")
        invoice_lines = invoice1.invoice_line_ids
        self.assertEqual(invoice_lines.product_id, self.product)
        self.assertEqual(invoice_lines.quantity, 10)
        invoice1.action_post()
        self.assertEqual(invoice1.state, 'posted')
