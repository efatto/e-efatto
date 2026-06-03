from datetime import timedelta

from odoo import fields
from odoo.fields import Command
from odoo.tests import Form, tagged

from odoo.addons.purchase_autocomplete_no_reference.tests import (
    test_purchase_autocomplete_no_reference as base_test,
)

PurchaseInvoiceNoReference = base_test.PurchaseInvoiceNoReference


@tagged("post_install", "-at_install")
class PurchaseAutocompleteQtyToInvoice(PurchaseInvoiceNoReference):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product2 = cls.env.ref("product.product_delivery_02")
        cls.user.write(
            {
                "name": cls.user.name + " & purchaseman!",
                "groups_id": [
                    Command.link(cls.env.ref("purchase.group_purchase_user").id),
                    Command.link(
                        cls.env.ref("product_cost_security.group_product_cost").id
                    ),
                ],
            }
        )

    def _create_purchase_order(self, qty, qty1, ref):
        with Form(self.env["purchase.order"]) as purchase_form:
            purchase_form.date_order = fields.Date.today()
            purchase_form.partner_id = self.vendor
            purchase_form.partner_ref = ref
            with purchase_form.order_line.new() as purchase_line_form:
                # this is a service, it won't generate a stock move
                purchase_line_form.product_id = self.product
                purchase_line_form.product_qty = qty
                purchase_line_form.product_uom = self.product.uom_po_id
                purchase_line_form.price_unit = self.product.list_price
                purchase_line_form.name = self.product.name
                purchase_line_form.date_planned = fields.Date.today() + timedelta(
                    days=20
                )
            with purchase_form.order_line.new() as purchase_line_form:
                purchase_line_form.product_id = self.product2
                purchase_line_form.product_qty = qty1
                purchase_line_form.product_uom = self.product2.uom_po_id
                purchase_line_form.price_unit = self.product2.list_price
                purchase_line_form.name = self.product2.name
                purchase_line_form.date_planned = fields.Date.today() + timedelta(
                    days=20
                )
            purchase_order = purchase_form.save()
        purchase_order.button_confirm()
        self.assertEqual(
            len(purchase_order.order_line), 2, msg="Order line was not created"
        )
        picking = purchase_order.picking_ids
        # set done to half of the quantity of the products
        picking.action_assign()
        picking.move_ids.quantity = qty1 / 2
        res = picking.button_validate()
        Form(self.env[res["res_model"]].with_context(**res["context"])).save().process()
        backorder_picking = purchase_order.picking_ids - picking
        self.assertTrue(backorder_picking)
        return purchase_order

    def test_00_purchase_order(self):
        # create first purchase order
        self._create_purchase_order(20, 50, "Vendor Reference ATCPO")
        # create a second purchase order
        self._create_purchase_order(70, 90, "Vendor Reference ATCPO1")
        # create vendor invoice
        invoice = self.init_invoice(
            move_type="in_invoice",
            journal=self.purchase_journal,
            partner=self.vendor,
            post=False,
        )
        invoice.ref = "Invoice Reference"
        invoice.invoice_line_ids = [
            self._prepare_invoice_line(
                product_id=self.product2,
                quantity=1.0,
                price_unit=100.0,
            )
        ]
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        # purchase.bill.union is created only when at least one vendor invoice exists
        # add first purchase order, it will add 2 rows
        vendor_bill_purchase_id = self.env["purchase.bill.union"].search(
            [("reference", "=", "Vendor Reference ATCPO")]
        )
        self.assertTrue(vendor_bill_purchase_id)
        invoice_form = Form(invoice)
        invoice_form.purchase_vendor_bill_id = vendor_bill_purchase_id
        invoice_form.save()
        self.assertEqual(len(invoice.invoice_line_ids), 3)
        # add second purchase order, it will add other 2 rows
        vendor_bill_purchase_id = self.env["purchase.bill.union"].search(
            [("reference", "=", "Vendor Reference ATCPO1")]
        )
        self.assertTrue(vendor_bill_purchase_id)
        invoice_form = Form(invoice)
        invoice_form.purchase_vendor_bill_id = vendor_bill_purchase_id
        invoice1 = invoice_form.save()
        self.assertEqual(invoice1.ref, "Invoice Reference")
        invoice_lines = invoice1.invoice_line_ids
        self.assertEqual(len(invoice_lines), 5)
        self.assertRecordValues(
            invoice_lines,
            [
                {"quantity": 1},
                {"quantity": 20},
                {"quantity": 25},
                {"quantity": 70},
                {"quantity": 45},
            ],
        )
        invoice1.action_post()
        self.assertEqual(invoice1.state, "posted")
