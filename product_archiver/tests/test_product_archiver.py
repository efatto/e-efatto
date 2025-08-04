from datetime import timedelta

from odoo import fields
from odoo.tests.common import Form, SavepointCase
from odoo.tools import mute_logger


class ProductArchiver(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.user_model = cls.env["res.users"].with_context(no_reset_password=True)
        cls.product = cls.env.ref("product.product_product_1")

    @mute_logger("odoo.models", "odoo.models.unlink", "odoo.addons.base.ir.ir_model")
    def test_archive_product(self):
        today_date = fields.Date.today()
        from_date = today_date - timedelta(days=1)
        old_date = today_date - timedelta(days=10)
        old_service = self.env["product.product"].create(
            {
                "name": "Old service",
                "default_code": "OLD_S_CODE",
                "type": "service",
            }
        )
        old_service.create_date = old_date.strftime("%Y-%m-%d")
        old_product = self.env["product.product"].create(
            {
                "name": "Old product",
                "default_code": "OLD_P_CODE",
                "type": "consu",
            }
        )
        old_product.create_date = old_date.strftime("%Y-%m-%d")
        self.product.create_date = today_date.strftime("%Y-%m-%d")
        new_product = self.env["product.product"].create(
            {
                "name": "New product",
                "default_code": "NEW_P_CODE",
                "type": "consu",
            }
        )
        wizard_form = Form(self.env["product.archiver"])
        wizard_form.from_date = from_date
        wizard = wizard_form.save()
        res = wizard.archive()
        domain = res.get("domain")
        model = res.get("res_model")
        moved_products = (
            self.env["stock.move.line"]
            .search([("date", ">=", from_date)])
            .mapped("product_id.product_tmpl_id")
        )
        products = self.env[model].search(domain)
        for moved_product in moved_products:
            self.assertFalse(moved_product in products)
        self.assertFalse(self.product.product_tmpl_id in products)
        self.assertFalse(new_product.product_tmpl_id in products)
        self.assertTrue(old_product.product_tmpl_id in products)
        self.assertTrue(old_service.active)
