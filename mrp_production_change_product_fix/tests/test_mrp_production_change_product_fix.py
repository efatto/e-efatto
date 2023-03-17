from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestMrpProductionChangeQty(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create({
            "name": "Component",
            "type": "product",
        })
        cls.product1 = cls.env["product.product"].create({
            "name": "Component1",
            "type": "product",
        })
        cls.main_bom.write({
            "bom_line_ids": [
                (0, 0, {"product_id": cls.product1.id, "product_qty": 10})
            ]
        })

    def test_update_product_qty(self):
        # bom_3 (product_6) = product_2:12 + product_4:8 [normal]
        # -> bom_2 (product_5):2 = product_3:3 [phantom]
        # -> bom_1 (product_4):2 = product_2:2 + subproduct_1_1:4 [normal]
        # total 4 mo lines: product_2:12, product_4:8, product_4:4, product_3:6
        man_order = self.env['mrp.production'].create({
            'name': 'MO-Test',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': 1,
            'bom_id': self.main_bom.id,
        })
        self.assertEqual(len(man_order.move_raw_ids), 4)
        old_move_raws = [x for x in man_order.move_raw_ids]
        self.env['change.production.qty'].create({
            'mo_id': man_order.id,
            'product_qty': man_order.product_qty,
        }).change_prod_qty()
        new_move_raws = [x for x in man_order.move_raw_ids]
        self.assertEqual(old_move_raws, new_move_raws)
        self.assertEqual(len(man_order.move_raw_ids), 4)
        # change from product1 to product in 1 line in top bom
        bom_line = self.main_bom.bom_line_ids.filtered(
            lambda x: x.product_id == self.product1
        )
        bom_line.write({'product_id': self.product.id})
        self.assertIn(self.product, self.main_bom.bom_line_ids.mapped("product_id"))
        self.env['change.production.qty'].create({
            'mo_id': man_order.id,
            'product_qty': man_order.product_qty,
        }).change_prod_qty()
        self.assertEqual(len(man_order.move_raw_ids), 4)
        self.assertIn(self.product, man_order.move_raw_ids.mapped("product_id"))

        # change product in 1 line in sub-bom phantom
        bom_line = self.sub_bom1.bom_line_ids.filtered(
            lambda x: x.product_id == self.subproduct_1_1
        )
        bom_line.write({'product_id': self.product.id})
        self.env['change.production.qty'].create({
            'mo_id': man_order.id,
            'product_qty': man_order.product_qty,
        }).change_prod_qty()
        self.assertEqual(len(man_order.move_raw_ids), 4)
        self.assertIn(self.product, man_order.move_raw_ids.mapped("product_id"))

        # remove 1 line in sub-bom phantom
        self.sub_bom2.bom_line_ids.filtered(
            lambda x: x.product_id.id == self.subproduct_1_1.id).unlink()
        self.env['change.production.qty'].create({
            'mo_id': man_order.id,
            'product_qty': man_order.product_qty,
        }).change_prod_qty()
        self.assertEqual(len(man_order.move_raw_ids.filtered(
            lambda x: x.state != "cancel"
        )), 3)
