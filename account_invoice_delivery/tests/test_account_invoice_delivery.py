# Copyright 2018 Tecnativa - Pedro M. Baeza
# Copyright 2024 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import Form, common, tagged


def _execute_onchanges(records, field_name):
    """Helper methods that executes all onchanges associated to a field."""
    for onchange in records._onchange_methods.get(field_name, []):
        for record in records:
            onchange(record)


@tagged("post_install", "-at_install")
class TestDeliveryAutoRefresh(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        service = cls.env["product.product"].create(
            {"name": "Service Test", "type": "service"}
        )
        pricelist = cls.env["product.pricelist"].create(
            {"name": "Test pricelist", "currency_id": cls.env.company.currency_id.id}
        )
        carrier_form = Form(cls.env["delivery.carrier"])
        carrier_form.name = "Test carrier 1"
        carrier_form.delivery_type = "base_on_rule"
        carrier_form.product_id = service
        with carrier_form.price_rule_ids.new() as price_rule_form:
            price_rule_form.variable = "weight"
            price_rule_form.operator = "<="
            price_rule_form.max_value = 20
            price_rule_form.list_base_price = 50
        with carrier_form.price_rule_ids.new() as price_rule_form:
            price_rule_form.variable = "weight"
            price_rule_form.operator = "<="
            price_rule_form.max_value = 40
            price_rule_form.list_base_price = 30
            price_rule_form.list_price = 1
            price_rule_form.variable_factor = "weight"
        with carrier_form.price_rule_ids.new() as price_rule_form:
            price_rule_form.variable = "weight"
            price_rule_form.operator = ">"
            price_rule_form.max_value = 40
            price_rule_form.list_base_price = 20
            price_rule_form.list_price = 1.5
            price_rule_form.variable_factor = "weight"
        cls.carrier_1 = carrier_form.save()
        carrier_form = Form(cls.env["delivery.carrier"])
        carrier_form.name = "Test carrier 2"
        carrier_form.delivery_type = "base_on_rule"
        carrier_form.product_id = service
        with carrier_form.price_rule_ids.new() as price_rule_form:
            price_rule_form.variable = "weight"
            price_rule_form.operator = "<="
            price_rule_form.max_value = 20
            price_rule_form.list_base_price = 50
        cls.carrier_2 = carrier_form.save()
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "weight": 10, "list_price": 20}
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
                "property_delivery_carrier_id": cls.carrier_1.id,
                "property_product_pricelist": pricelist.id,
            }
        )
        cls.param_name1 = "delivery_auto_refresh.auto_add_delivery_line"
        order_form = Form(cls.env["sale.order"])
        order_form.partner_id = cls.partner
        order_form.partner_invoice_id = cls.partner
        order_form.partner_shipping_id = cls.partner
        order_form.carrier_id = cls.carrier_1
        with order_form.order_line.new() as ol_form:
            ol_form.product_id = cls.product
            ol_form.product_uom_qty = 2
        cls.order = order_form.save()

    def test_auto_refresh_invoice_from_so(self):
        self.assertFalse(self.order.order_line.filtered("is_delivery"))
        self.env["ir.config_parameter"].sudo().set_param(self.param_name1, 1)
        self.order.write(
            {"order_line": [(1, self.order.order_line.id, {"product_uom_qty": 3})]}
        )
        self.order.order_line.filtered("is_delivery")
        self._confirm_sale_order(self.order)
        invoice = self._create_invoice_from_so(self.order)
        self.assertEqual(invoice.delivery_carrier_id, self.order.carrier_id)
        # line2 = self.order.order_line.new(
        #     {
        #         "order_id": self.order.id,
        #         "product_id": self.product.id,
        #         "product_uom_qty": 2,
        #     }
        # )
        # _execute_onchanges(line2, "product_id")
        # vals = line2._convert_to_write(line2._cache)
        # del vals["order_id"]
        # self.order.write({"order_line": [(0, 0, vals)]})
        # line_delivery = self.order.order_line.filtered("is_delivery")
        # self.assertEqual(line_delivery.price_unit, 95)
        # # Test saving the discount
        # line_delivery.discount = 10
        # self.order.carrier_id = self.carrier_2
        # line_delivery = self.order.order_line.filtered("is_delivery")
        # self.assertEqual(line_delivery.discount, 10)
        # # Test change the carrier_id using the wizard
        # wiz = Form(
        #     self.env["choose.delivery.carrier"].with_context(
        #         {
        #             "default_order_id": self.order.id,
        #             "default_carrier_id": self.carrier_1.id,
        #         }
        #     )
        # ).save()
        # wiz.button_confirm()
        # self.assertEqual(self.order.carrier_id, self.carrier_1)
        # line_delivery = self.order.order_line.filtered("is_delivery")
        # self.assertEqual(line_delivery.name, "Test carrier 1")

    @staticmethod
    def _confirm_sale_order(order):
        sale_form = Form(order)
        # Force the delivery line creation
        with sale_form.order_line.edit(0) as line_form:
            line_form.product_uom_qty = 2
        sale_form.save()
        line_delivery = order.order_line.filtered("is_delivery")
        order.action_confirm()
        return line_delivery

    @staticmethod
    def _create_invoice_from_so(order):
        picking = order.picking_ids[0]
        for sml in picking.move_lines.mapped("move_line_ids"):
            sml.qty_done = sml.product_qty
        picking._action_done()
        order._create_invoices()
        invoice = order.invoice_ids[0]
        return invoice

    def _test_autorefresh_unlink_line(self):
        """Helper method to test the possible cases for voiding the line"""
        self.assertFalse(self.order.order_line.filtered("is_delivery"))
        self.env["ir.config_parameter"].sudo().set_param(self.param_name1, 1)
        sale_form = Form(self.order)
        # Force the delivery line creation
        with sale_form.order_line.edit(0) as line_form:
            line_form.product_uom_qty = 2
        sale_form.save()
        return self.order.order_line.filtered("is_delivery")

    def test_auto_refresh_so_and_unlink_line(self):
        """The return wasn't flagged to refund, so the delivered qty won't
        change, thus the delivery line shouldn't be either"""
        self._test_autorefresh_unlink_line()
        delivery_line = self.order.order_line.filtered("is_delivery")
        sale_form = Form(self.order)
        sale_form.order_line.remove(0)
        sale_form.save()
        self.assertFalse(delivery_line.exists())

    def test_auto_add_delivery_line_add_service(self):
        self.env["ir.config_parameter"].sudo().set_param(self.param_name1, 1)
        service = self.env["product.product"].create(
            {"name": "Service Test", "type": "service"}
        )
        invoice_form = Form(self.env["account.move"])
        invoice_form.partner_id = self.partner
        invoice_form.partner_shipping_id = self.partner
        with invoice_form.invoice_line_ids.new() as il_form:
            il_form.product_id = service
            il_form.quantity = 2
            il_form.account_id = (
                service.property_account_income_id
                or service.categ_id.property_account_income_categ_id
            )
        invoice = invoice_form.save()
        delivery_line = invoice.invoice_line_ids.filtered("is_delivery")
        self.assertFalse(delivery_line.exists())

    def test_auto_refresh_so_and_manually_unlink_delivery_line(self):
        """Test that we are able to manually remove the delivery line"""
        self._test_autorefresh_unlink_line()
        invoice = self._create_invoice_from_so(self.order)
        invoice_form = Form(invoice)
        # Deleting the delivery line
        invoice_form.invoice_line_ids.remove(1)
        invoice_form.save()
