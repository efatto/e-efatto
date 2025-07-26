from odoo.tests import Form
from odoo.tests.common import SavepointCase


class TestSaleDeliveryRecreate(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref("base.res_partner_2")
        # Acoustic Bloc Screens, 16 on hand
        cls.product1 = cls.env.ref("product.product_product_25")
        # Cabinet with Doors, 8 on hand
        cls.product2 = cls.env.ref("product.product_product_10")
        # Large Cabinet, 250 on hand
        cls.product3 = cls.env.ref("product.product_product_6")
        cls.product1.invoice_policy = "order"
        vendor1 = cls.env["res.partner"].create(
            {"name": "AAA", "email": "from.test@example.com"}
        )
        supplier_info1 = cls.env["product.supplierinfo"].create(
            {
                "name": vendor1.id,
                "price": 50,
            }
        )
        route_buy = cls.env.ref("purchase_stock.route_warehouse0_buy")
        warehouse1 = cls.env.ref("stock.warehouse0")
        route_mto = warehouse1.mto_pull_id.route_id
        cls.product2.write(
            {
                "seller_ids": [(6, 0, [supplier_info1.id])],
                "route_ids": [(6, 0, [route_buy.id, route_mto.id])],
            }
        )

    def test_complete_picking_from_sale(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line:
            line.product_id = self.product1
            line.product_uom_qty = 5
            line.price_unit = 100
        with order_form.order_line.new() as line:
            line.product_id = self.product2
            line.product_uom_qty = 10
            line.price_unit = 100
        order = order_form.save()
        order.action_confirm()
        self.assertEqual(order.state, "sale")
        self.assertEqual(len(order.picking_ids), 1)
        order.picking_ids[0].action_cancel()
        order.picking_ids[0].unlink()
        self.assertEqual(len(order.picking_ids), 0)
        order.delivery_recreate()
        self.assertEqual(len(order.picking_ids), 1)
        po = self.env["purchase.order"].search([("origin", "=", order.name)])
        self.assertEqual(sum(po.mapped("order_line.product_qty")), 10)

    def test_partial_picking_from_sale(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line:
            line.product_id = self.product1
            line.product_uom_qty = 5
            line.price_unit = 100
        with order_form.order_line.new() as line:
            line.product_id = self.product2
            line.product_uom_qty = 10
            line.price_unit = 100
        order1 = order_form.save()
        order1.action_confirm()
        self.assertEqual(order1.state, "sale")
        picking = order1.picking_ids[0]
        self.assertEqual(sum(picking.mapped("move_lines.product_uom_qty")), 15)
        picking.move_lines[0].move_line_ids[0].qty_done = 3
        backorder_wiz_id = picking.button_validate()["res_id"]
        backorder_wiz = self.env["stock.backorder.confirmation"].browse(
            backorder_wiz_id
        )
        backorder_wiz.process()
        self.assertEqual(len(order1.picking_ids), 2)
        picking1 = order1.picking_ids - picking
        picking1.action_cancel()
        picking1.unlink()
        self.assertEqual(len(order1.picking_ids), 1)
        order1.delivery_recreate()
        self.assertEqual(len(order1.picking_ids), 2)
        self.assertEqual(
            sum(order1.picking_ids.mapped("move_lines.product_uom_qty")), 15
        )
        po1 = self.env["purchase.order"].search([("origin", "=", order1.name)])
        self.assertEqual(sum(po1.mapped("order_line.product_qty")), 10)
