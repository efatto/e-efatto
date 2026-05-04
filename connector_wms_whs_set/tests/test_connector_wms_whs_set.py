from odoo.exceptions import ValidationError
from odoo.tests import Form, tagged

from odoo.addons.connector_wms_whs.tests.test_connector_wms_whs import (
    TestConnectorWmsWhs,
)


@tagged("-standard", "test_wms")
class TestConnectorWmsWhsSet(TestConnectorWmsWhs):
    def setUp(self):
        super().setUp()
        self.causali.update(
            {
                "out_robot": "12",
            }
        )
        self.product_for_set = self.product_model.search(
            [
                ("default_code", "=", "PRODUCT_FOR_SET"),
            ]
        )
        if not self.product_for_set:
            self.workcenter1.mrp_set_position = "left"
            self.workcenter2 = self.env["mrp.workcenter"].create(
                {
                    "name": "Base Workcenter 2",
                    "capacity": 1,
                    "time_start": 10,
                    "time_stop": 5,
                    "time_efficiency": 80,
                    "costs_hour": 23.0,
                    "mrp_set_position": "right",
                    "alternative_workcenter_ids": [(6, 0, self.workcenter1.ids)],
                }
            )
            self.workcenter1.alternative_workcenter_ids = self.workcenter2.ids
            product_form = Form(self.env["product.product"])
            product_form.name = "Product for set"
            product_form.default_code = "PRODUCT_FOR_SET"
            product_form.type = "product"
            product_form.route_ids.add(self.warehouse.mto_pull_id.route_id)
            product_form.route_ids.add(self.warehouse.manufacture_pull_id.route_id)
            self.product_for_set = product_form.save()
            # todo create bom with purchased components and operation1 should be ok
            bom_form = Form(self.env["mrp.bom"])
            bom_form.product_id = self.product_for_set
            bom_form.product_tmpl_id = self.product_for_set.product_tmpl_id
            bom_form.type = "normal"
            bom = bom_form.save()
            bom.write(
                {
                    "operation_ids": [(6, 0, self.operation1.ids)],
                    "bom_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product1.id,
                            },
                        )
                    ],
                }
            )

    def _mrp_partial_from_sale_set(self, left_order, right_order, wrong_products=False):
        production_set_form = Form(self.env["mrp.production.set"])
        production_set_form.production_left_id = left_order
        production_set_form.production_right_id = right_order
        if wrong_products:
            with self.assertRaises(ValidationError):
                production_set_form.save()
            return True
        production_set = production_set_form.save()
        self.assertEqual(production_set.state, "confirmed")
        production_set_form = Form(production_set)
        production_set_form.qty_producing_left = 5
        production_set = production_set_form.save()
        production_set.button_update_qty_producing()
        self.assertEqual(production_set.state, "progress")
        production_set.button_send_to_whs()
        self.assertEqual(production_set.sent_to_whs, True)
        self.assertEqual(left_order.sent_to_whs, True)
        self.assertEqual(right_order.sent_to_whs, True)
        self.assertEqual(left_order.qty_producing, production_set.qty_producing_left)
        self.assertEqual(right_order.qty_producing, production_set.qty_producing_right)
        self.assertEqual(
            left_order.move_raw_ids.whs_list_ids.num_lista,
            right_order.move_raw_ids.whs_list_ids.num_lista,
        )
        self.assertEqual(left_order.move_raw_ids.whs_list_ids.riga, 1)
        self.assertEqual(right_order.move_raw_ids.whs_list_ids.riga, 2)
        return True

    def test_00_mrp_partial_from_sale_set(self):
        # productions done in a set must share the same num_lista, the left will be
        # the row number 1, the right will be the row number 2
        self.top_product.categ_id = self.categ_id
        self.assertNotEqual(self.top_product.categ_id.name, "CUSTOM")
        left_order = self._create_sale_order_with_mrp(self.top_product)
        right_order = self._create_sale_order_with_mrp(self.top_product)
        self._mrp_partial_from_sale_set(left_order, right_order, wrong_products=True)
        left_order = self._create_sale_order_with_mrp(self.product_for_set)
        right_order = self._create_sale_order_with_mrp(self.product_for_set)
        self.assertEqual(left_order.state, "confirmed")
        self.assertEqual(right_order.state, "confirmed")
        left_order.button_plan()
        right_order.button_plan()
        self._mrp_partial_from_sale_set(left_order, right_order)

    # def test_08_mrp_partial_from_sale_custom(self):
    #     # todo productions in set must share the same lista, the left will be
    #     #  the row 1, the right will be the row 2
    #     self.top_product.categ_id = self.custom_categ_id
    #     self.assertEqual(self.top_product.categ_id.name, "CUSTOM")
    #     self._mrp_partial_from_sale(self._create_sale_order_with_mrp(), is_custom=True)
    #
    # def test_09_mrp_total_from_sale(self):
    #     # todo productions in set must share the same lista, the left will be
    #     #  the row 1, the right will be the row 2
    #     self.top_product.categ_id = self.categ_id
    #     self.assertNotEqual(self.top_product.categ_id.name, "CUSTOM")
    #     self._mrp_total_from_sale()
    #
    # def test_09_mrp_total_from_sale_custom(self):
    #     # todo productions in set must share the same lista, the left will be
    #     #  the row 1, the right will be the row 2
    #     self.top_product.categ_id = self.custom_categ_id
    #     self.assertEqual(self.top_product.categ_id.name, "CUSTOM")
    #     self._mrp_total_from_sale(is_custom=True)
