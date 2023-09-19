# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests.common import SavepointCase


class PurchaseInvoiceNoReference(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.user_model = cls.env["res.users"].with_context(no_reset_password=True)
        cls.vendor = cls.env.ref("base.res_partner_3")
        cls.product = cls.env.ref("product.product_product_1")
        cls.purchase_journal = (
            cls.env["account.journal"]
            .with_company(cls.env.user.company_id.id)
            .search(
                [
                    ("type", "=", "purchase"),
                ],
                limit=1,
            )
        )
        cls.expense_account = cls.env["account.account"].create(
            {
                "code": "TEST_EXPENSE",
                "name": "Expenses account",
                "user_type_id": cls.env.ref("account.data_account_type_expenses").id,
            }
        )

    def test_purchase_order(self):
        purchase_order = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "date_order": fields.Date.today(),
                "partner_ref": "Vendor Reference",
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 20,
                            "product_uom": self.product.uom_po_id.id,
                            "price_unit": self.product.list_price,
                            "name": self.product.name,
                            "date_planned": fields.Date.today() + timedelta(days=20),
                        },
                    ),
                ],
            }
        )
        purchase_order.button_confirm()
        self.assertEqual(
            len(purchase_order.order_line), 1, msg="Order line was not created"
        )
        account_invoice = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "invoice_date": fields.Date.today(),
                "currency_id": self.env.ref("base.EUR").id,
                "journal_id": self.purchase_journal.id,
                "company_id": self.env.user.company_id.id,
                "partner_id": self.vendor.id,
                "date": fields.Date.today(),
                "ref": "Invoice Reference",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref("product.product_product_5").id,
                            "quantity": 5,
                            "account_id": self.expense_account.id,
                            "name": "product test 5",
                            "price_unit": 6,
                            "currency_id": self.env.ref("base.EUR").id,
                        },
                    ),
                ],
            }
        )
        account_invoice.action_post()
        vendor_bill_purchase_id = self.env["purchase.bill.union"].search(
            [("reference", "=", "Vendor Reference")]
        )
        self.assertTrue(vendor_bill_purchase_id)
        account_invoice.vendor_bill_purchase_id = vendor_bill_purchase_id
        self.assertEqual(account_invoice.ref, "Invoice Reference")
