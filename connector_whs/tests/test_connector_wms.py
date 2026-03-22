# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


@tagged("-standard", "test_wms")
class CommonConnectorWMS(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dbsource_model = cls.env["base.external.dbsource"]
        cls.stock_location_model = cls.env["stock.location"]
        cls.product_model = cls.env["product.product"]
        cls.dest_location = cls.env.ref("stock.stock_location_customers")
        cls.src_location = cls.env.ref("stock.stock_location_stock")  # noqa
        cls.wms_location = cls.stock_location_model.search(
            [
                ("name", "=", "WMS Location (child of default internal location)"),
            ]
        )
        if not cls.wms_location:
            cls.wms_location = cls.stock_location_model.create(
                {
                    "name": "WMS Location (child of default internal location)",
                    "location_id": cls.src_location.id,
                }
            )
        cls.manufacture_location = cls.stock_location_model.search(
            [("usage", "=", "production")], limit=1
        )[0]
        cls.procurement_model = cls.env["procurement.group"]
        cls.partner = cls.env.ref("base.res_partner_2")
        # Create product with 11 on hand on WMS location and 5 in default Stock location
        # Odoo gets products from all internal locations in the warehouse by default
        cls.product1 = cls.product_model.search(
            [
                ("default_code", "=", "PRODUCT1"),
            ]
        )
        if not cls.product1:
            cls.product1 = cls.product_model.create(
                [
                    {
                        "name": "test product1",
                        "default_code": "PRODUCT1",
                        "type": "consu",
                        "is_storable": True,
                    }
                ]
            )
        cls.StockQuant = cls.env["stock.quant"]
        cls.quant_product1 = cls.StockQuant.search(
            [
                ("product_id", "=", cls.product1.id),
                ("quantity", "=", 11.0),
            ]
        )
        if not cls.quant_product1:
            cls.quant_product1 = cls.StockQuant.create(
                [
                    {
                        "product_id": cls.product1.id,
                        "location_id": cls.wms_location.id,
                        "quantity": 11.0,
                    }
                ]
            )
        cls.quant_product1_1 = cls.StockQuant.search(
            [
                ("product_id", "=", cls.product1.id),
                ("quantity", "=", 5.0),
            ]
        )
        if not cls.quant_product1_1:
            cls.quant_product1_1 = cls.StockQuant.create(
                [
                    {
                        "product_id": cls.product1.id,
                        "location_id": cls.src_location.id,
                        "quantity": 5.0,
                    }
                ]
            )
        # Create product with 8 on hand
        cls.product2 = cls.product_model.search(
            [
                ("default_code", "=", "PRODUCT2"),
            ]
        )
        if not cls.product2:
            cls.product2 = cls.product_model.create(
                [
                    {
                        "name": "test product2",
                        "default_code": "PRODUCT2",
                        "type": "consu",
                        "is_storable": True,
                    }
                ]
            )
        cls.quant_product2 = cls.StockQuant.search(
            [
                ("product_id", "=", cls.product2.id),
                ("quantity", "=", 8.0),
            ]
        )
        if not cls.quant_product2:
            cls.quant_product2 = cls.StockQuant.create(
                [
                    {
                        "product_id": cls.product2.id,
                        "location_id": cls.wms_location.id,
                        "quantity": 8.0,
                    }
                ]
            )
        # create product excluded from WMS with 10 on hand
        cls.product_excluded = cls.product_model.search(
            [
                ("default_code", "=", "PRODUCTEX"),
            ]
        )
        if not cls.product_excluded:
            cls.product_excluded = cls.product_model.create(
                [
                    {
                        "name": "test product excluded from WMS",
                        "default_code": "PRODUCTEX",
                        "type": "consu",
                        "is_storable": True,
                        "exclude_from_whs": True,
                    }
                ]
            )
        cls.quant_product_excluded = cls.StockQuant.search(
            [
                ("product_id", "=", cls.product_excluded.id),
                ("quantity", "=", 10.0),
            ]
        )
        if not cls.quant_product_excluded:
            cls.quant_product_excluded = cls.StockQuant.create(
                [
                    {
                        "product_id": cls.product_excluded.id,
                        "location_id": cls.src_location.id,
                        "quantity": 10.0,
                    }
                ]
            )
        # Large Cabinet, 250 on hand
        cls.product3 = cls.env.ref("product.product_product_6")
        # Drawer Black, 0 on hand
        cls.product4 = cls.env.ref("product.product_product_16")
        cls.product5 = cls.env.ref("product.product_product_20")
        cls.product1.invoice_policy = "order"
        cls.product1.write(
            {
                "customer_ids": [
                    (
                        0,
                        0,
                        {
                            "partner_id": cls.partner.id,
                            "product_code": "CUSTOMERCODE",
                            "product_name": "Product customer name",
                        },
                    )
                ]
            }
        )
        cls.product2.invoice_policy = "order"
        # MRP data
        cls.top_product = cls.env.ref(
            "mrp_production_demo.product_product_manufacture_1"
        )
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.user.company_id.id)],
            limit=1,
        )
        cls.warehouse.mto_pull_id.route_id.active = True
        cls.top_product.write(
            dict(
                route_ids=[
                    (
                        6,
                        0,
                        [
                            cls.warehouse.mto_pull_id.route_id.id,
                            cls.warehouse.manufacture_pull_id.route_id.id,
                        ],
                    ),
                ]
            )
        )
        cls.subproduct1 = cls.env.ref(
            "mrp_production_demo.product_product_manufacture_1_1"
        )
        cls.subproduct2 = cls.env.ref(
            "mrp_production_demo.product_product_manufacture_1_2"
        )
        cls.subproduct_1_1 = cls.env.ref(
            "mrp_production_demo.product_product_manufacture_1_1_1"
        )
        cls.subproduct_1_1.write(
            dict(
                route_ids=[
                    (
                        6,
                        0,
                        [
                            cls.warehouse.mto_pull_id.route_id.id,
                            cls.env.ref("purchase_stock.route_warehouse0_buy").id,
                        ],
                    ),
                ]
            )
        )
        cls.subproduct_2_1 = cls.env.ref(
            "mrp_production_demo.product_product_manufacture_1_2_1"
        )
        cls.main_bom = cls.env.ref("mrp_production_demo.mrp_bom_manuf_1")
        cls.sub_bom_phantom_1 = cls.env.ref("mrp_production_demo.mrp_bom_manuf_1_1")
        cls.sub_bom_phantom_2 = cls.env.ref("mrp_production_demo.mrp_bom_manuf_1_2")
        cls.sub_bom_normal_1 = cls.env.ref("mrp_production_demo.mrp_bom_manuf_1_3")
        cls.workcenter1 = cls.env["mrp.workcenter"].create(
            {
                "name": "Base Workcenter",
                "default_capacity": 1,
                "time_start": 10,
                "time_stop": 5,
                "time_efficiency": 80,
                "costs_hour": 23.0,
            }
        )
        cls.operation1 = cls.env["mrp.routing.workcenter"].search(
            [
                ("name", "=", "Operation 1"),
                ("workcenter_id", "=", cls.workcenter1.id),
            ]
        )
        if not cls.operation1:
            cls.operation1 = cls.env["mrp.routing.workcenter"].create(
                {
                    "name": "Operation 1",
                    "workcenter_id": cls.workcenter1.id,
                    "bom_id": cls.main_bom.id,
                    "time_mode": "manual",
                    "time_cycle_manual": 90,
                    "sequence": 1,
                }
            )
        cls.mrp_user = cls.env.ref("base.user_demo")
        cls.mrp_user.write(
            {
                "groups_id": [(4, cls.env.ref("mrp.group_mrp_user").id)],
            }
        )

    def run_stock_procurement_scheduler(self):
        with mute_logger("odoo.addons.stock.models.procurement"):
            self.procurement_model.run_scheduler()
            time.sleep(15)

    @staticmethod
    def _auto_fill_consumed_qty(moves):
        for move in moves:
            move.quantity = move.product_uom_qty
