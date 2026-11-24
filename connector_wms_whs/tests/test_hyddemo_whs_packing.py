# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import json
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestHyddemoWhsPacking(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dbsource = cls.env["base.external.dbsource"].create(
            {
                "name": "WMS packing test source",
                "connector": "mssql",
                "conn_string": "mssql+pymssql://user:password@localhost/dbname",
                "company_id": cls.env.company.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Packing test product",
                "default_code": "C34100005",
                "type": "consu",
                "is_storable": True,
            }
        )
        cls.payload = {
            "PackingId": 1,
            "Packages": [
                {
                    "SerialCode": "BOX00000001",
                    "PackageType": "EURO PALLET",
                    "Dimension": {
                        "WeightKg": 12.5,
                        "WidthCm": 80.0,
                        "HeightCm": 100.0,
                        "DepthCm": 120.0,
                    },
                    "Contents": [
                        {
                            "LogisticSN": "SN00000004",
                            "ItemId": "C34100005",
                            "Lot": "2436",
                            "Lot2": "",
                            "Lot3": "9796",
                            "Qty": 1.0,
                            "OrderNumber": "M-176081",
                            "RowNumber": "821965",
                        },
                        {
                            "LogisticSN": "PK00000003",
                            "ItemId": "C34100005",
                            "Lot": "2436",
                            "Lot2": "",
                            "Lot3": "9796",
                            "Qty": 9.0,
                            "OrderNumber": "M-176082",
                            "RowNumber": "821966",
                        },
                    ],
                },
                {
                    "SerialCode": "BOX00000002",
                    "PackageType": "SCATOLA",
                    "Dimension": {
                        "WeightKg": 0.0,
                        "WidthCm": 0.0,
                        "HeightCm": 0.0,
                        "DepthCm": 0.0,
                    },
                    "Contents": [
                        {
                            "LogisticSN": "SN00000007",
                            "ItemId": "C34100005",
                            "Lot": "2436",
                            "Lot2": "",
                            "Lot3": "9796",
                            "Qty": 1.0,
                            "OrderNumber": "M-176081",
                            "RowNumber": "821965",
                        }
                    ],
                },
            ],
        }

    def test_create_from_payload(self):
        packing = self.env["hyddemo.whs.packing"]._create_from_wms_payload(
            self.dbsource, 1, self.payload
        )
        self.assertEqual(packing.name, "1")
        self.assertEqual(packing.dbsource_id, self.dbsource)
        self.assertEqual(packing.company_id, self.env.company)
        self.assertEqual(packing.package_count, 2)
        self.assertEqual(packing.content_count, 3)

        box1 = packing.package_ids.filtered(
            lambda package: package.serial_code == "BOX00000001"
        )
        self.assertEqual(len(box1), 1)
        # package type and measures are free text/values from the WMS operator
        self.assertEqual(box1.package_type, "EURO PALLET")
        self.assertAlmostEqual(box1.weight_kg, 12.5)
        self.assertAlmostEqual(box1.width_cm, 80.0)
        self.assertAlmostEqual(box1.height_cm, 100.0)
        self.assertAlmostEqual(box1.depth_cm, 120.0)
        self.assertEqual(len(box1.content_ids), 2)

        content = box1.content_ids.filtered(
            lambda line: line.logistic_sn == "PK00000003"
        )
        self.assertEqual(content.item_code, "C34100005")
        self.assertEqual(content.product_id, self.product)
        self.assertEqual(content.lot, "2436")
        self.assertFalse(content.lot2)
        self.assertEqual(content.lot3, "9796")
        self.assertAlmostEqual(content.qty, 9.0)
        self.assertEqual(content.order_number, "M-176082")
        self.assertEqual(content.row_number, "821966")

    def test_read_same_packing_twice_refreshes(self):
        packing = self.env["hyddemo.whs.packing"]._create_from_wms_payload(
            self.dbsource, 1, self.payload
        )
        payload = dict(
            self.payload,
            Packages=[
                {
                    "SerialCode": "BOX00000001",
                    "PackageType": "PALLET",
                    "Dimension": {"WeightKg": 20.0},
                    "Contents": [
                        {
                            "LogisticSN": "SN00000004",
                            "ItemId": "C34100005",
                            "Qty": 2.0,
                        }
                    ],
                }
            ],
        )
        new_packing = self.env["hyddemo.whs.packing"]._create_from_wms_payload(
            self.dbsource, 1, payload
        )
        self.assertEqual(new_packing, packing)
        self.assertEqual(
            self.env["hyddemo.whs.packing"].search_count(
                [("dbsource_id", "=", self.dbsource.id), ("name", "=", "1")]
            ),
            1,
        )
        self.assertEqual(packing.package_count, 1)
        self.assertEqual(packing.content_count, 1)
        self.assertEqual(packing.package_ids.package_type, "PALLET")
        self.assertAlmostEqual(packing.package_ids.weight_kg, 20.0)

    def test_payload_without_packing_id_is_skipped(self):
        packing = self.env["hyddemo.whs.packing"]._create_from_wms_payload(
            self.dbsource, False, {}
        )
        self.assertFalse(packing)

    def test_payload_as_package_list(self):
        packing = self.env["hyddemo.whs.packing"]._create_from_wms_payload(
            self.dbsource, "2", self.payload["Packages"]
        )
        self.assertEqual(packing.name, "2")
        self.assertEqual(packing.package_count, 2)

    def test_read_packages_from_wms(self):
        calls = []

        def fake_connection_open_mssql(record):
            return object()

        def fake_execute_mssql(record, sqlquery, sqlparams, metadata):
            calls.append((sqlquery, sqlparams, metadata))
            if sqlquery.startswith("SELECT"):
                return [
                    (1, json.dumps(self.payload).encode("utf-8")),
                ], ["PackingId", "JsonData"]
            return [], []

        with (
            patch.object(
                type(self.dbsource),
                "connection_open_mssql",
                fake_connection_open_mssql,
            ),
            patch.object(
                type(self.dbsource),
                "execute_mssql",
                fake_execute_mssql,
            ),
        ):
            self.dbsource.whs_read_packages()

        packing = self.env["hyddemo.whs.packing"].search(
            [("dbsource_id", "=", self.dbsource.id), ("name", "=", "1")]
        )
        self.assertEqual(len(packing), 1)
        self.assertEqual(packing.package_count, 2)
        self.assertEqual(packing.content_count, 3)
        update_queries = [
            call for call in calls if call[0].startswith("UPDATE HOST_PACKING")
        ]
        self.assertEqual(len(update_queries), 1)
        self.assertEqual(update_queries[0][1], {"PackingId": 1})
