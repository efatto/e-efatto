
from odoo.tests.common import SavepointCase
from odoo.tools import mute_logger
from odoo import fields


class StockProcurementDraftPurchase(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.user_model = cls.env['res.users'].with_context(no_reset_password=True)
        cls.partner = cls.env.ref('base.res_partner_2')
        cls.partner.customer = True
        cls.procurement = cls.env['procurement.group']
        buy = cls.env.ref('purchase_stock.route_warehouse0_buy')
        cls.vendor = cls.env.ref('base.res_partner_3')
        supplierinfo = cls.env['product.supplierinfo'].create({
            'name': cls.vendor.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Product Test',
            'standard_price': 50.0,
            'seller_ids': [(6, 0, [supplierinfo.id])],
            'route_ids': [(6, 0, [buy.id])],
        })
        cls.op_model = cls.env['stock.warehouse.orderpoint']
        cls.warehouse = cls.env.ref('stock.warehouse0')
        cls.manual_procurement_wiz = cls.env['make.procurement.orderpoint']
        # Create User:
        cls.test_user = cls.env['res.users'].create({
            'name': 'John',
            'login': 'test',
        })
        cls.op1 = cls.op_model.create([{
            'name': 'Orderpoint_1',
            'warehouse_id': cls.warehouse.id,
            'location_id': cls.warehouse.lot_stock_id.id,
            'product_id': cls.product.id,
            'product_min_qty': 10.0,
            'product_max_qty': 50.0,
            'qty_multiple': 1.0,
            'product_uom': cls.product.uom_id.id,
            'include_draft_purchase': True,
        }])

    def _create_sale_order_line(self, order, product, qty, commitment_date=False):
        vals = {
            'order_id': order.id,
            'product_id': product.id,
            'product_uom_qty': qty,
            'price_unit': 100,
            }
        if commitment_date:
            vals.update({
                'commitment_date': fields.Datetime.now()
            })
        line = self.env['sale.order.line'].create(vals)
        line.product_id_change()
        line._convert_to_write(line._cache)
        return line

    def manual_procurement(self, orderpoint, user):
        """Make Procurement from Reordering Rule"""
        context = {
            'active_model': 'stock.warehouse.orderpoint',
            'active_ids': orderpoint.ids,
            'active_id': orderpoint.id
        }
        wizard = self.manual_procurement_wiz.sudo(user).\
            with_context(context).create({})
        wizard.make_procurement()
        return wizard

    @mute_logger(
        'odoo.models', 'odoo.models.unlink', 'odoo.addons.base.ir.ir_model'
    )
    def test_00_procurement(self):
        self.assertEqual(self.op1.product_location_qty, 0)
        self.assertEqual(self.op1.incoming_location_qty, 0)
        self.assertEqual(self.op1.draft_purchase_order_qty, 0)
        self.assertEqual(self.op1.outgoing_location_qty, 0)
        self.assertEqual(self.op1.virtual_location_qty, 0)
        self.assertEqual(self.op1.virtual_location_draft_purchase_qty, 0)
        # launch scheduler, it will order 50 pc of product
        self.manual_procurement(self.op1, self.test_user)
        self.op1.refresh()
        self.assertEqual(self.op1.draft_purchase_order_qty, 50)
        self.assertEqual(self.op1.virtual_location_draft_purchase_qty, 50)
        purchase_orders = self.env['purchase.order'].search([
            ('origin', '=', 'Orderpoint_1')
        ])
        self.assertEqual(len(purchase_orders), 1)
        purchase_order1 = purchase_orders[0]
        purchase_line = purchase_order1.order_line.filtered(
            lambda x: x.product_id.id == self.product.id
        )
        self.assertEqual(purchase_line.product_uom_qty, 50)
        self.assertEqual(purchase_order1.state, 'draft')
        purchase_order1.print_quotation()
        self.assertEqual(purchase_order1.state, 'sent')
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self._create_sale_order_line(order1, self.product, 5)
        order1.action_confirm()
        self.manual_procurement(self.op1, self.test_user)
        # check that no other RdP are created for this op
        purchase_orders = self.env['purchase.order'].search([
            ('origin', '=', 'Orderpoint_1'),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(purchase_orders), 0)

        # de-activate option to include draft purchase
        self.op1.include_draft_purchase = False
        self.manual_procurement(self.op1, self.test_user)
        # check that one RdP is created for this op
        purchase_orders = self.env['purchase.order'].search([
            ('origin', '=', 'Orderpoint_1'),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(purchase_orders), 1)
