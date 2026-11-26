from odoo.tests import TransactionCase


class TestListPriceNotCopied(TransactionCase):
    """Duplicating a product must not carry its sales price over."""

    def setUp(self):
        super().setUp()
        self.price = 42.0
        self.default_price = self.env["product.template"].default_get(["list_price"])[
            "list_price"
        ]
        self.template = self.env["product.template"].create(
            {"name": "Test product", "list_price": self.price}
        )

    def test_copy_template_keeps_price_of_original(self):
        self.template.copy()
        self.assertEqual(self.template.list_price, self.price)

    def test_copy_template_does_not_copy_list_price(self):
        duplicate = self.template.copy()
        self.assertNotEqual(duplicate.list_price, self.price)
        self.assertEqual(duplicate.list_price, self.default_price)

    def test_copy_variant_does_not_copy_list_price(self):
        duplicate = self.template.product_variant_id.copy()
        self.assertNotEqual(duplicate.list_price, self.price)
        self.assertEqual(duplicate.list_price, self.default_price)
