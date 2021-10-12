# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase
from odoo import fields
from datetime import timedelta


class ProductArchiver(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env.ref('product.product_product_1')

    def test_archive_product(self):
        today_date = fields.Date.today()
        from_date = today_date - timedelta(days=1)
        old_date = today_date - timedelta(days=10)
        old_product = self.env['product.product'].create({
            'name': 'Old product',
        })
        old_product.create_date = old_date.strftime('%Y-%m-%d')
        self.product.create_date = today_date.strftime('%Y-%m-%d')
        new_product = self.env['product.product'].create({
            'name': 'New product',
        })
        wizard_obj = self.env['product.archiver']
        wizard_vals = wizard_obj.default_get(
                ['model']
            )
        wizard_vals.update({'from_date': from_date})
        wizard = wizard_obj.create(wizard_vals)
        res = wizard.archive()
        domain = res.get('domain')
        model = res.get('res_model')
        moved_products = self.env['stock.move.line'].search([
            ('date', '>=', from_date)
        ]).mapped('product_id')
        products = self.env[model].search(domain)
        for moved_product in moved_products:
            self.assertFalse(moved_product in products)
        self.assertFalse(self.product in products)
        self.assertFalse(new_product in products)
        self.assertTrue(old_product in products)
