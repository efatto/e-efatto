from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestMrpBomEvaluation(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service_product = cls.env["product.product"].create({
            "name": "Service product",
            "type": "service",
            "uom_id": cls.env.ref("uom.product_uom_hour").id,
            "uom_po_id": cls.env.ref("uom.product_uom_hour").id,
        })
        cls.routing1.write({
            'product_id': cls.service_product.id,
        })
        cls.main_bom.write({
            "bom_evaluation_line_ids": [
                (0, 0, {
                    "product_id": cls.service_product.id,
                    "product_qty": 5,
                    "product_uom_id": cls.service_product.uom_id.id,
                })
            ]
        })

    def test_01_get_price_from_product_and_total(self):
        pass
