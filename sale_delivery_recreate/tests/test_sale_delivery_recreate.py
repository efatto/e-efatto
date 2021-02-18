# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestSaleDeliveryRecreate(TransactionCase):

    def _create_sale_order_line(self, order, product, qty):
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': product.id,
            'product_uom_qty': qty,
            'price_unit': 100,
            })
        line.product_id_change()
        line._convert_to_write(line._cache)
        return line

    def setUp(self):
        super(TestSaleDeliveryRecreate, self).setUp()
        self.partner = self.env.ref('base.res_partner_2')
        # Acoustic Bloc Screens, 16 on hand
        self.product1 = self.env.ref('product.product_product_25')
        # Cabinet with Doors, 8 on hand
        self.product2 = self.env.ref('product.product_product_10')
        # Large Cabinet, 250 on hand
        self.product3 = self.env.ref('product.product_product_6')
        self.product1.invoice_policy = 'order'
        vendor1 = self.env['res.partner'].create(
            {'name': 'AAA', 'email': 'from.test@example.com'})
        supplier_info1 = self.env['product.supplierinfo'].create({
            'name': vendor1.id,
            'price': 50,
        })
        route_buy = self.ref('purchase_stock.route_warehouse0_buy')
        warehouse1 = self.env.ref('stock.warehouse0')
        route_mto = warehouse1.mto_pull_id.route_id.id
        self.product2.write({
            'seller_ids': [(6, 0, [supplier_info1.id])],
            'route_ids': [(6, 0, [route_buy, route_mto])]
        })

    def test_complete_picking_from_sale(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self._create_sale_order_line(order, self.product1, 5)
        self._create_sale_order_line(order, self.product2, 10)
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        self.assertEqual(len(order.picking_ids), 1)
        order.picking_ids[0].action_cancel()
        order.picking_ids[0].unlink()
        self.assertEqual(len(order.picking_ids), 0)
        order.delivery_recreate()
        self.assertEqual(len(order.picking_ids), 1)
        po = self.env['purchase.order'].search([('origin', '=', order.name)])
        self.assertEqual(sum(po.mapped('order_line.product_qty')), 10)

    def test_partial_picking_from_sale(self):
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self._create_sale_order_line(order1, self.product1, 5)
        self._create_sale_order_line(order1, self.product2, 10)
        order1.action_confirm()
        self.assertEqual(order1.state, 'sale')
        picking = order1.picking_ids[0]
        self.assertEqual(sum(picking.mapped('move_lines.product_uom_qty')), 15)
        picking.move_lines[0].move_line_ids[0].qty_done = 3
        backorder_wiz_id = picking.button_validate()['res_id']
        backorder_wiz = self.env['stock.backorder.confirmation'].browse(
            backorder_wiz_id)
        backorder_wiz.process()
        self.assertEqual(len(order1.picking_ids), 2)
        picking1 = order1.picking_ids - picking
        picking1.action_cancel()
        picking1.unlink()
        self.assertEqual(len(order1.picking_ids), 1)
        order1.delivery_recreate()
        self.assertEqual(len(order1.picking_ids), 2)
        self.assertEqual(
            sum(order1.picking_ids.mapped('move_lines.product_uom_qty')), 15)
        po1 = self.env['purchase.order'].search([('origin', '=', order1.name)])
        self.assertEqual(sum(po1.mapped('order_line.product_qty')), 10)
