# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase
from odoo import fields
from odoo.tools import float_round


class TestPurchaseUpdateLastSupplierinfo(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_model = cls.env['product.template']
        cls.product_template = cls.product_model.create({
            'name': 'Product test',
            'type': 'product',
            'uom_id': cls.env.ref('uom.product_uom_meter').id,
            'uom_po_id': cls.env.ref('uom.product_uom_meter').id,
            'list_price': 50.0,
            'taxes_id': [(6, 0, cls.env['account.tax'].search(
                [('type_tax_use', '=', 'sale')], limit=1).ids)],
            'supplier_taxes_id': [(6, 0, cls.env['account.tax'].search(
                [('type_tax_use', '=', 'purchase')], limit=1).ids)],
            'seller_ids': [
                (0, 0, {
                    'name': cls.env.ref('base.res_partner_3').id,
                    'price': 5.0,
                    'discount': 10.0,
                    'min_qty': 0.0,
                }),
                (0, 0, {
                    'name': cls.env.ref('base.res_partner_3').id,
                    'price': 5.0,
                    'min_qty': 0.0,
                    'date_end': fields.Date.today(),
                }),
                (0, 0, {
                    'name': cls.env.ref('base.res_partner_2').id,
                    'price': 5.0,
                    'min_qty': 0.0,
                })
            ]
        })
        cls.product = cls.env['product.product'].search([
            ('product_tmpl_id', '=', cls.product_template.id)
        ], limit=1)
        cls.uom_po = cls.env['uom.uom'].create({
            'name': 'Bar 6 meter',
            'category_id': cls.env.ref('uom.uom_categ_length').id,
            'uom_type': 'bigger',
            'factor_inv': 6.0,
        })
        cls.product_template_uom_po = cls.product_model.create({
            'name': 'Product with uom po',
            'type': 'product',
            'uom_id': cls.env.ref('uom.product_uom_meter').id,
            'uom_po_id': cls.uom_po.id,
            'list_price': 50.0,
            'taxes_id': [(6, 0, cls.env['account.tax'].search(
                [('type_tax_use', '=', 'sale')], limit=1).ids)],
            'supplier_taxes_id': [(6, 0, cls.env['account.tax'].search(
                [('type_tax_use', '=', 'purchase')], limit=1).ids)],
            'weight': 3.15,
            'weight_uom_id': cls.env.ref('uom.product_uom_qt').id,
            'seller_ids': [
                (0, 0, {
                    'name': cls.env.ref('base.res_partner_3').id,
                    'price': 3.49,
                    'min_qty': 0.0,
                })
            ]
        })
        cls.product_uom_po = cls.env['product.product'].search([
            ('product_tmpl_id', '=', cls.product_template_uom_po.id)
        ], limit=1)

    def test_00_purchase_order(self):
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'date_order': fields.Date.today(),
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_qty': 20,
                    'product_uom': self.product.uom_po_id.id,
                    'price_unit': self.product.list_price,
                    'name': self.product.name,
                    'date_planned': fields.Date.today(),
                }),
            ]
        })

        purchase_line = purchase_order.order_line[0]
        purchase_line._onchange_quantity()
        self.assertEqual(
            len(purchase_order.order_line), 1, msg="Order line was not created")
        self.assertAlmostEqual(purchase_line.price_unit, 5, 2)
        purchase_order.button_confirm()
        self.assertEqual(purchase_order.state, 'purchase')
        seller = self.product.seller_ids.filtered(
            lambda x: x.name == purchase_order.partner_id and x.sequence == 1
        )
        self.assertAlmostEqual(seller.price, purchase_line.price_unit)
        self.assertAlmostEqual(seller.discount, purchase_line.discount)

    def test_01_purchase_order_different_uom_po(self):
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.env.ref('base.res_partner_3').id,
            'date_order': fields.Date.today(),
            'order_line': [
                (0, 0, {
                    'product_id': self.product_uom_po.id,
                    'product_qty': 20,
                    'product_uom': self.product_uom_po.uom_po_id.id,
                    'price_unit': self.product_uom_po.list_price,
                    'name': self.product_uom_po.name,
                    'date_planned': fields.Date.today(),
                }),
            ]
        })

        purchase_line = purchase_order.order_line[0]
        purchase_line._onchange_quantity()
        self.assertEqual(
            len(purchase_order.order_line), 1, msg="Order line was not created")
        self.assertAlmostEqual(purchase_line.price_unit, 3.49, 2)
        purchase_order.button_confirm()
        self.assertEqual(purchase_order.state, 'purchase')
        seller = self.product_uom_po.seller_ids.filtered(
            lambda x: x.name == purchase_order.partner_id and x.sequence == 1
        )
        self.assertAlmostEqual(seller.price, purchase_line.price_unit)
        self.assertAlmostEqual(seller.discount, purchase_line.discount)
