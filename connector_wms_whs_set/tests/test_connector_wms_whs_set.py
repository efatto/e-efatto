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

    def _mrp_partial_from_sale_set(self, man_orders, wrong_products=False):
        man_order = man_orders[0]
        man_order1 = man_orders[1]
        production_set_form = Form(self.env["mrp.production.set"])
        production_set_form.production_left_id = man_order
        production_set_form.production_right_id = man_order1
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
        self.assertEqual(man_order.sent_to_whs, True)
        self.assertEqual(man_order1.sent_to_whs, True)
        self.assertEqual(man_order.qty_producing, production_set.qty_producing_left)
        self.assertEqual(man_order1.qty_producing, production_set.qty_producing_right)
        self.assertEqual(
            man_order.move_raw_ids.whs_list_ids.num_lista,
            man_order1.move_raw_ids.whs_list_ids.num_lista,
        )
        self.assertEqual(man_order.move_raw_ids.whs_list_ids.riga, 1)
        self.assertEqual(man_order1.move_raw_ids.whs_list_ids.riga, 2)
        return True

    def test_00_mrp_partial_from_sale_set(self):
        # productions done in a set must share the same num_lista, the left will be
        # the row number 1, the right will be the row number 2
        self.top_product.categ_id = self.categ_id
        self.assertNotEqual(self.top_product.categ_id.name, "CUSTOM")
        man_order = self._create_sale_order_with_mrp(self.top_product)
        man_order1 = self._create_sale_order_with_mrp(self.top_product)
        self._mrp_partial_from_sale_set((man_order | man_order1), wrong_products=True)
        man_order = self._create_sale_order_with_mrp(self.product_for_set)
        man_order1 = self._create_sale_order_with_mrp(self.product_for_set)
        self._mrp_partial_from_sale_set(man_order | man_order1)

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
