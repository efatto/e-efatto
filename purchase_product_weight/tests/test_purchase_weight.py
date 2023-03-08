# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo import fields
from odoo.tools import float_round


class PurchaseProductWeight(TransactionCase):

    def setUp(self):
        super(PurchaseProductWeight, self).setUp()
        self.product_model = self.env['product.template']
        self.product_template_on_weight = self.product_model.create({
            'name': 'Product on weight',
            'type': 'product',
            'uom_id': self.env.ref('uom.product_uom_meter').id,
            'uom_po_id': self.env.ref('uom.product_uom_meter').id,
            'list_price': 50.0,
            'taxes_id': [(6, 0, self.env['account.tax'].search(
                [('type_tax_use', '=', 'sale')], limit=1).ids)],
            'supplier_taxes_id': [(6, 0, self.env['account.tax'].search(
                [('type_tax_use', '=', 'purchase')], limit=1).ids)],
            'compute_price_on_weight': True,
            'weight': 0.15,
            'weight_uom_id': self.env.ref('uom.product_uom_ton').id,
            'seller_ids': [
                (0, 0, {
                    'name': self.env.ref('base.res_partner_3').id,
                    'price': 5.0,
                    'min_qty': 0.0,
                })
            ]
        })
        self.product_on_weight = self.env['product.product'].search([
            ('product_tmpl_id', '=', self.product_template_on_weight.id)
        ], limit=1)
        self.uom_po = self.env['uom.uom'].create({
            'name': 'Bar 6 meter',
            'category_id': self.env.ref('uom.uom_categ_length').id,
            'uom_type': 'bigger',
            'factor_inv': 6.0,
        })
        self.product_template_on_weight_uom_po = self.product_model.create({
            'name': 'Product on weight with uom po',
            'type': 'product',
            'uom_id': self.env.ref('uom.product_uom_meter').id,
            'uom_po_id': self.uom_po.id,
            'list_price': 50.0,
            'taxes_id': [(6, 0, self.env['account.tax'].search(
                [('type_tax_use', '=', 'sale')], limit=1).ids)],
            'supplier_taxes_id': [(6, 0, self.env['account.tax'].search(
                [('type_tax_use', '=', 'purchase')], limit=1).ids)],
            'compute_price_on_weight': True,
            'weight': 3.15,
            'weight_uom_id': self.env.ref('uom.product_uom_qt').id,
            'seller_ids': [
                (0, 0, {
                    'name': self.env.ref('base.res_partner_3').id,
                    'price': 3.49,
                    'min_qty': 0.0,
                })
            ]
        })
        self.product_on_weight_uom_po = self.env['product.product'].search([
            ('product_tmpl_id', '=', self.product_template_on_weight_uom_po.id)
        ], limit=1)

    def test_purchase_order_on_weight(self):
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.env.ref('base.res_partner_3').id,
            'date_order': fields.Date.today(),
            'order_line': [
                (0, 0, {
                    'product_id': self.product_on_weight.id,
                    'product_qty': 20,
                    'product_uom': self.product_on_weight.uom_po_id.id,
                    'price_unit': self.product_on_weight.list_price,
                    'name': self.product_on_weight.name,
                    'date_planned': fields.Date.today(),
                }),
            ]
        })

        purchase_line = purchase_order.order_line[0]
        purchase_line._onchange_quantity()
        self.assertEqual(
            len(purchase_order.order_line), 1, msg="Order line was not created")
        self.assertAlmostEqual(purchase_line.price_unit, 5 * 0.15, 2)
        self.assertAlmostEqual(purchase_line.weight_total, 20 * 0.15, 2)
        self.assertAlmostEqual(purchase_line.weight_price_unit, 5, 2)
        purchase_line.product_qty = 25
        purchase_line._onchange_quantity()
        self.assertAlmostEqual(purchase_line.price_unit, 5 * 0.15, 2)
        self.assertAlmostEqual(purchase_line.weight_total, 25 * 0.15, 2)
        self.assertAlmostEqual(purchase_line.weight_price_unit, 5, 2)
        purchase_line.weight_price_unit = 7.77
        purchase_line._onchange_weight_price_unit()
        line_price = float_round(
            7.77 * 0.15,
            self.env['decimal.precision'].precision_get('Product Price')
        )
        self.assertAlmostEqual(purchase_line.price_unit, line_price)
        self.assertAlmostEqual(purchase_line.weight_total, 25 * 0.15, 2)
        self.assertAlmostEqual(purchase_line.weight_price_unit, 7.77, 2)
        purchase_line.product_qty = 25
        purchase_line._onchange_quantity()
        self.assertAlmostEqual(purchase_line.price_unit, 5 * 0.15, 2)
        self.assertAlmostEqual(purchase_line.weight_total, 25 * 0.15, 2)
        self.assertAlmostEqual(purchase_line.weight_price_unit, 5, 2)

    def test_purchase_order_on_weight_different_uom_po(self):
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.env.ref('base.res_partner_3').id,
            'date_order': fields.Date.today(),
            'order_line': [
                (0, 0, {
                    'product_id': self.product_on_weight_uom_po.id,
                    'product_qty': 20,
                    'product_uom': self.product_on_weight_uom_po.uom_po_id.id,
                    'price_unit': self.product_on_weight_uom_po.list_price,
                    'name': self.product_on_weight_uom_po.name,
                    'date_planned': fields.Date.today(),
                }),
            ]
        })

        purchase_line = purchase_order.order_line[0]
        purchase_line._onchange_quantity()
        self.assertEqual(
            len(purchase_order.order_line), 1, msg="Order line was not created")
        self.assertAlmostEqual(purchase_line.price_unit, 3.49 * 3.15 * 6, 2)
        self.assertAlmostEqual(purchase_line.weight_total, 20 * 3.15 * 6, 2)
        self.assertAlmostEqual(purchase_line.weight_price_unit, 3.49, 2)
        purchase_line.product_qty = 25
        purchase_line._onchange_quantity()
        self.assertAlmostEqual(purchase_line.price_unit, 3.49 * 3.15 * 6, 2)
        self.assertAlmostEqual(purchase_line.weight_total, 25 * 3.15 * 6, 2)
        self.assertAlmostEqual(purchase_line.weight_price_unit, 3.49, 2)
        purchase_line.weight_price_unit = 0.03
        purchase_line._onchange_weight_price_unit()
        line_price = float_round(
            0.03 * 3.15 * 6,
            self.env['decimal.precision'].precision_get('Product Price')
        )
        self.assertAlmostEqual(purchase_line.price_unit, line_price)
        self.assertAlmostEqual(purchase_line.weight_total, 25 * 3.15 * 6, 2)
        self.assertAlmostEqual(purchase_line.weight_price_unit, 0.03, 2)
        purchase_line.product_qty = 25
        purchase_line._onchange_quantity()
        self.assertAlmostEqual(purchase_line.price_unit, 3.49 * 3.15 * 6, 2)
        self.assertAlmostEqual(purchase_line.weight_total, 25 * 3.15 * 6, 2)
        self.assertAlmostEqual(purchase_line.weight_price_unit, 3.49, 2)
