# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger
from odoo import fields
from datetime import timedelta


class PurchaseSellerEvaluation(TransactionCase):

    def setUp(self):
        super(PurchaseSellerEvaluation, self).setUp()
        mto = self.env.ref('stock.route_warehouse0_mto')
        buy = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.product_model = self.env['product.template']
        self.product_template = self.product_model.create({
            'name': 'Product test',
            'type': 'product',
            'uom_id': self.env.ref('uom.product_uom_meter').id,
            'uom_po_id': self.env.ref('uom.product_uom_meter').id,
            'list_price': 50.0,
            'taxes_id': [(6, 0, self.env['account.tax'].search(
                [('type_tax_use', '=', 'sale')], limit=1).ids)],
            'supplier_taxes_id': [(6, 0, self.env['account.tax'].search(
                [('type_tax_use', '=', 'purchase')], limit=1).ids)],
            'weight': 0.15,
            'route_ids': [(6, 0, [buy.id, mto.id])],
            'seller_ids': [
                (0, 0, {
                    'name': self.env.ref('base.res_partner_3').id,
                    'price': 5.0,
                    'min_qty': 0.0,
                    'sequence': 1,
                    'date_start': fields.Date.today() - timedelta(days=100),
                }),
                (0, 0, {
                    'name': self.env.ref('base.res_partner_4').id,
                    'price': 4.0,
                    'min_qty': 0.0,
                    'sequence': 2,
                    'date_start': fields.Date.today() - timedelta(days=100),
                }),
                (0, 0, {
                    'name': self.env.ref('base.res_partner_1').id,
                    'price': 1.0,
                    'min_qty': 0.0,
                    'sequence': 3,
                    'date_start': fields.Date.today() - timedelta(days=100),
                    'date_end': fields.Date.today() - timedelta(days=50),
                }),
            ]
        })
        self.product = self.env['product.product'].search([
            ('product_tmpl_id', '=', self.product_template.id)
        ], limit=1)
        self.uom_po = self.env['uom.uom'].create({
            'name': 'Bar 6 meter',
            'category_id': self.env.ref('uom.uom_categ_length').id,
            'uom_type': 'bigger',
            'factor_inv': 6.0,
        })
        self.product_template_uom_po = self.product_model.create({
            'name': 'Product with uom po',
            'type': 'product',
            'uom_id': self.env.ref('uom.product_uom_meter').id,
            'uom_po_id': self.uom_po.id,
            'list_price': 50.0,
            'taxes_id': [(6, 0, self.env['account.tax'].search(
                [('type_tax_use', '=', 'sale')], limit=1).ids)],
            'supplier_taxes_id': [(6, 0, self.env['account.tax'].search(
                [('type_tax_use', '=', 'purchase')], limit=1).ids)],
            'weight': 0.15,
            'route_ids': [(6, 0, [buy.id, mto.id])],
            'seller_ids': [
                (0, 0, {
                    'name': self.env.ref('base.res_partner_3').id,
                    'price': 5.0,
                    'min_qty': 0.0,
                    'sequence': 1,
                    'date_start': fields.Date.today() - timedelta(days=100),
                }),
                (0, 0, {
                    'name': self.env.ref('base.res_partner_4').id,
                    'price': 4.0,
                    'min_qty': 0.0,
                    'sequence': 2,
                    'date_start': fields.Date.today() - timedelta(days=100),
                }),
                (0, 0, {
                    'name': self.env.ref('base.res_partner_1').id,
                    'price': 1.0,
                    'min_qty': 0.0,
                    'sequence': 3,
                    'date_start': fields.Date.today() - timedelta(days=100),
                    'date_end': fields.Date.today() - timedelta(days=50),
                }),
            ]
        })
        self.product_uom_po = self.env['product.product'].search([
            ('product_tmpl_id', '=', self.product_template_uom_po.id)
        ], limit=1)

    def test_sale_order(self):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_12').id,
            'date_order': fields.Date.today(),
            'picking_policy': 'direct',
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 20,
                    'product_uom': self.product.uom_po_id.id,
                    'price_unit': self.product.list_price,
                    'name': self.product.name,
                    'expected_date': fields.Date.today() + timedelta(days=20),
                }),
            ]
        })
        sale_order.action_confirm()
        with mute_logger('odoo.addons.stock.models.procurement'):
            self.env['procurement.group'].run_scheduler()
        self.assertEqual(
            len(sale_order.order_line), 1, msg="Order line was not created")
        purchase_order = self.env['purchase.order'].search([
            ('partner_id', '=', self.env.ref('base.res_partner_4').id),
            ('order_line.product_id', 'in', [self.product.id]),
        ])
        self.assertTrue(purchase_order)
        po_line = purchase_order.order_line.filtered(
            lambda x: x.product_id == self.product
        )
        price_unit = 4
        if purchase_order.partner_id.currency_id != purchase_order.currency_id:
            price_unit *= purchase_order.currency_id._get_conversion_rate(
                purchase_order.partner_id.currency_id, purchase_order.currency_id,
                purchase_order.company_id, purchase_order.date_order)
        self.assertEqual(po_line.price_unit, round(price_unit, 2))

    # def test_sale_order_different_uom_po(self):
    #     purchase_order = self.env['purchase.order'].create({
    #         'partner_id': self.env.ref('base.res_partner_3').id,
    #         'date_order': fields.Date.today(),
    #         'order_line': [
    #             (0, 0, {
    #                 'product_id': self.product_on_weight_uom_po.id,
    #                 'product_qty': 20,
    #                 'product_uom': self.product_on_weight_uom_po.uom_po_id.id,
    #                 'price_unit': self.product_on_weight_uom_po.list_price,
    #                 'name': self.product_on_weight_uom_po.name,
    #                 'date_planned': fields.Date.today(),
    #             }),
    #         ]
    #     })
    #
