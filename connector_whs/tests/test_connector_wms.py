# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


@tagged("-standard", "test_wms")
class CommonConnectorWMS(TransactionCase):
    def setUp(self):
        super().setUp()
        self.dbsource_model = self.env["base.external.dbsource"]
        self.dest_location = self.env.ref("stock.stock_location_customers")
        self.src_location = self.env.ref("stock.stock_location_stock")  # noqa
        self.wms_location = self.env["stock.location"].create(
            {
                "name": "WMS Location (child of default internal location)",
                "location_id": self.src_location.id,
            }
        )
        self.manufacture_location = self.env["stock.location"].search(
            [("usage", "=", "production")], limit=1
        )[0]
        self.procurement_model = self.env["procurement.group"]
        self.partner = self.env.ref("base.res_partner_2")
        # Create product with 11 on hand on WMS location and 5 in default Stock location
        # Odoo gets products from all internal locations in the warehouse by default
        self.product1 = self.env["product.product"].create(
            [
                {
                    "name": "test product1",
                    "default_code": "PRODUCT1",
                    "type": "product",
                }
            ]
        )
        self.StockQuant = self.env["stock.quant"]
        self.quant_product1 = self.StockQuant.create(
            [
                {
                    "product_id": self.product1.id,
                    "location_id": self.wms_location.id,
                    "quantity": 11.0,
                }
            ]
        )
        self.quant_product1 = self.StockQuant.create(
            [
                {
                    "product_id": self.product1.id,
                    "location_id": self.src_location.id,
                    "quantity": 5.0,
                }
            ]
        )
        # Create product with 8 on hand
        self.product2 = self.env["product.product"].create(
            [
                {
                    "name": "test product2",
                    "default_code": "PRODUCT2",
                    "type": "product",
                }
            ]
        )
        self.quant_product2 = self.StockQuant.create(
            [
                {
                    "product_id": self.product2.id,
                    "location_id": self.wms_location.id,
                    "quantity": 8.0,
                }
            ]
        )
        # create product excluded from WMS with 10 on hand
        self.product_excluded = self.env["product.product"].create(
            [
                {
                    "name": "test product excluded from WMS",
                    "default_code": "PRODUCT1",
                    "type": "product",
                    "exclude_from_whs": True,
                }
            ]
        )
        self.quant_product_excluded = self.StockQuant.create(
            [
                {
                    "product_id": self.product_excluded.id,
                    "location_id": self.src_location.id,
                    "quantity": 10.0,
                }
            ]
        )
        # Large Cabinet, 250 on hand
        self.product3 = self.env.ref("product.product_product_6")
        # Drawer Black, 0 on hand
        self.product4 = self.env.ref("product.product_product_16")
        self.product5 = self.env.ref("product.product_product_20")
        self.product1.invoice_policy = "order"
        self.product1.write(
            {
                "customer_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.partner.id,
                            "product_code": "CUSTOMERCODE",
                            "product_name": "Product customer name",
                        },
                    )
                ]
            }
        )
        self.product2.invoice_policy = "order"
        # MRP data
        self.top_product = self.env.ref(
            "mrp_production_demo.product_product_manufacture_1"
        )
        self.warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.user.company_id.id)],
            limit=1,
        )
        self.warehouse.mto_pull_id.route_id.active = True
        self.top_product.write(
            dict(
                route_ids=[
                    (
                        6,
                        0,
                        [
                            self.warehouse.mto_pull_id.route_id.id,
                            self.warehouse.manufacture_pull_id.route_id.id,
                        ],
                    ),
                ]
            )
        )
        self.subproduct1 = self.env.ref(
            "mrp_production_demo.product_product_manufacture_1_1"
        )
        self.subproduct2 = self.env.ref(
            "mrp_production_demo.product_product_manufacture_1_2"
        )
        self.subproduct_1_1 = self.env.ref(
            "mrp_production_demo.product_product_manufacture_1_1_1"
        )
        self.subproduct_1_1.write(
            dict(
                route_ids=[
                    (
                        6,
                        0,
                        [
                            self.warehouse.mto_pull_id.route_id.id,
                            self.env.ref("purchase_stock.route_warehouse0_buy").id,
                        ],
                    ),
                ]
            )
        )
        self.subproduct_2_1 = self.env.ref(
            "mrp_production_demo.product_product_manufacture_1_2_1"
        )
        self.main_bom = self.env.ref("mrp_production_demo.mrp_bom_manuf_1")
        self.sub_bom_phantom_1 = self.env.ref("mrp_production_demo.mrp_bom_manuf_1_1")
        self.sub_bom_phantom_2 = self.env.ref("mrp_production_demo.mrp_bom_manuf_1_2")
        self.sub_bom_normal_1 = self.env.ref("mrp_production_demo.mrp_bom_manuf_1_3")
        self.workcenter1 = self.env["mrp.workcenter"].create(
            {
                "name": "Base Workcenter",
                "capacity": 1,
                "time_start": 10,
                "time_stop": 5,
                "time_efficiency": 80,
                "costs_hour": 23.0,
            }
        )
        self.operation1 = self.env["mrp.routing.workcenter"].create(
            {
                "name": "Operation 1",
                "workcenter_id": self.workcenter1.id,
                "time_mode": "manual",
                "time_cycle_manual": 90,
                "sequence": 1,
            }
        )
        self.mrp_user = self.env.ref("base.user_demo")
        self.mrp_user.write(
            {
                "groups_id": [(4, self.env.ref("mrp.group_mrp_user").id)],
            }
        )

    def run_stock_procurement_scheduler(self):
        with mute_logger("odoo.addons.stock.models.procurement"):
            self.procurement_model.run_scheduler()
            time.sleep(15)

    @staticmethod
    def _auto_fill_consumed_qty(moves):
        for move in moves:
            move.quantity_done = move.product_uom_qty
