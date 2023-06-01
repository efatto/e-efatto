from odoo.tests.common import SavepointCase


class TestMrpBomEvaluation(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Product = cls.env["product.product"]
        cls.service_product = cls.Product.create({
            "name": "Service product",
            "type": "service",
            "uom_id": cls.env.ref("uom.product_uom_hour").id,
            "uom_po_id": cls.env.ref("uom.product_uom_hour").id,
        })
        cls.subproduct_1 = cls.Product.create([{
            "name": "Subproduct 1",
            "type": "product",
            "standard_price": 10.0,
        }])
        cls.subproduct_2 = cls.Product.create([{
            "name": "Subproduct 2",
            "type": "product",
            "standard_price": 15.0,
        }])
        cls.workcenter1 = cls.env["mrp.workcenter"].create({
            "name": "Base Workcenter",
            "capacity": 1,
            "time_start": 10,
            "time_stop": 5,
            "time_efficiency": 80,
            "costs_hour": 23.0,
            "product_id": cls.service_product.id,
        })
        cls.routing1 = cls.env["mrp.routing"].create({
            "name": "Simple routing",
        })
        cls.operation1 = cls.env["mrp.routing.workcenter"].create({
            "name": "Operation 1",
            "workcenter_id": cls.workcenter1.id,
            "routing_id": cls.routing1.id,
            "time_mode": "manual",
            "time_cycle_manual": 90,
            "sequence": 1,
        })
        cls.mrp_user = cls.env.ref("base.user_demo")
        cls.mrp_user.write({
            "groups_id": [(4, cls.env.ref("mrp.group_mrp_user").id)],
        })
        cls.top_product = cls.Product.create([{
            "name": "Top Product",
            "type": "product",
            "route_ids": [
                (6, 0, [cls.env.ref("stock.route_warehouse0_mto").id,
                        cls.env.ref("mrp.route_warehouse0_manufacture").id]),
            ],
        }])
        cls.main_bom = cls.env["mrp.bom.evaluation"].create({
            "product_tmpl_id": cls.top_product.product_tmpl_id.id
        })

    def create_bom_line(self, product, qty):
        line = self.env["mrp.bom.line.evaluation"].create({
            "bom_id": self.main_bom.id,
            "product_id": product.id,
            "product_tmpl_id": product.product_tmpl_id.id,
            "product_qty": qty,
            "product_uom_id": product.uom_id.id,
        })
        line.onchange_product_id()
        line._convert_to_write(line._cache)
        return line

    def test_01_get_price_from_product_and_total(self):
        # check price and standard price for subproducts in bom are the first ones
        self.create_bom_line(self.subproduct_1, 5)
        self.create_bom_line(self.subproduct_2, 7)
        bom_evaluation_line_1_1 = self.main_bom.bom_evaluation_line_ids.filtered(
            lambda x: x.product_id == self.subproduct_1
        )
        self.assertEqual(bom_evaluation_line_1_1.price_unit,
                         self.subproduct_1.standard_price)
        # change standard price for subproducts

        # put subproducts in main bom
        # check price and price write date are the last ones
        pass
