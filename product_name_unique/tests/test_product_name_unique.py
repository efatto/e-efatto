from odoo.exceptions import ValidationError
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestProductNameUnique(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, test_product_name_unique=True))
        cls.product2 = cls.env.ref("product.product_product_5")
        cls.product2_name = cls.product2.name
        cls.product2_new_name = "New Product Name"
        cls.product1 = cls.env.ref("product.product_product_1")
        cls.product2_name = cls.product2.name

    def test_01_check_after_installation(self):
        self.assertEqual(self.product2.name, self.product2_name)
        with Form(self.product2) as product_form:
            product_form.name = self.product2_new_name
            product_form.save()
        self.assertEqual(self.product2.name, self.product2_new_name)

    def test_02_check_no_duplication(self):
        with Form(self.product2) as product_form:
            product_form.name = self.product2_new_name
            product_form.save()
        self.assertEqual(self.product2.name, self.product2_new_name)
        with self.assertRaises(ValidationError):
            with Form(self.product1) as product_form:
                product_form.name = self.product2_new_name
                product_form.save()
