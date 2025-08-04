from odoo.tests import Form
from odoo.tests.common import SavepointCase
from odoo.tools import mute_logger


class TestSaleDeliveryRecreate(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.procurement_model = cls.env["procurement.group"]
        cls.partner = cls.env.ref("base.res_partner_2")
        # Acoustic Bloc Screens, 16 on hand
        cls.product1 = cls.env.ref("product.product_product_25")
        # Large Cabinet, 250 on hand
        cls.product3 = cls.env.ref("product.product_product_6")
        cls.product1.invoice_policy = "order"
        vendor = cls.env["res.partner"].create(
            {"name": "AAA", "email": "from.test@example.com"}
        )
        supplier_info_form = Form(cls.env["product.supplierinfo"])
        supplier_info_form.name = vendor
        supplier_info_form.price = 50
        supplier_info = supplier_info_form.save()
        route_buy = cls.env.ref("purchase_stock.route_warehouse0_buy")
        warehouse1 = cls.env.ref("stock.warehouse0")
        route_mto = warehouse1.mto_pull_id.route_id
        route_mto.active = True
        cls.product2 = cls.env["product.product"].create(
            {
                "name": "Test Cabinet",
                "type": "product",
                "seller_ids": [(6, 0, [supplier_info.id])],
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
        with mute_logger("odoo.addons.stock.models.procurement"):
            self.procurement_model.run_scheduler()
        po = self.env["purchase.order"].search([("origin", "=", order.name)])
        self.assertEqual(sum(po.mapped("order_line.product_qty")), 10)
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
        po1 = self.env["purchase.order"].search([("origin", "=", order1.name)])
        self.assertEqual(sum(po1.mapped("order_line.product_qty")), 10)
        picking = order1.picking_ids[0]
        self.assertEqual(sum(picking.mapped("move_lines.product_uom_qty")), 15)
        picking.move_lines[0].move_line_ids[0].qty_done = 3
        res = picking.button_validate()
        Form(self.env[res["res_model"]].with_context(res["context"])).save().process()
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
