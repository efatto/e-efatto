# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import SavepointCase
from odoo.tests import Form
from odoo import fields


class TestPurchaseSaleMrpLink(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.user_model = cls.env['res.users'].with_context(no_reset_password=True)
        cls.vendor = cls.env.ref('base.res_partner_3')
        cls.partner = cls.env.ref('base.res_partner_2')
        cls.partner.customer = True
        cls.product = cls.env.ref('product.product_product_1')
        #todo creare un preventivo di vendita con prodotti e prodotti con bom
        #todo creare un RDP a fornitore con alcuni prodotti collegabili e altri no
        #todo lanciare il wizard

    def _create_sale_order(self):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': '5.0'
            })]
        })
        return sale_order

    def _create_purchase_order(self):
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
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
        return purchase_order

    def test_sale_link_product_simple(self):
        sale_order = self._create_sale_order()
        purchase_order = self._create_purchase_order()
        purchase_order.order_line[0]._onchange_quantity()
        self.assertEqual(
            len(purchase_order.order_line), 1, msg="Order line was not created")
        wizard_obj = self.env['purchase.sale.mrp.link.wizard']
        wizard_vals = wizard_obj.with_context(
                active_id=purchase_order.id,
                active_ids=[purchase_order.id],
                active_model='purchase.order',
            ).default_get(['purchase_order_id'])
        wizard_vals.update({
            'sale_order_id': sale_order.id,
        })
        wizard = wizard_obj.create(wizard_vals)
        wizard.action_done()
        self.assertEqual(
            purchase_order.sale_order_ids.ids, sale_order.ids
        )
