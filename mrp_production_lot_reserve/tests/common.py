# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.base.tests.common import BaseCommon


class Common(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
            }
        )
        (
            cls.free_lot,
            cls.reserved_move_lot,
            cls.reserved_prod_lot,
            cls.producing_lot,
        ) = cls.env["stock.lot"].create(
            [
                {
                    "name": f"Test {name} Lot",
                    "product_id": cls.product.id,
                }
                for name in [
                    "free",
                    "reserved by Move",
                    "reserved by Production",
                    "being produced",
                ]
            ]
        )

        cls.assigned_move = cls.env["stock.move"].create(
            {
                "name": "Test assign Lot",
                "location_id": cls.supplier_location.id,
                "location_dest_id": cls.stock_location.id,
                "product_id": cls.product.id,
                "product_uom_qty": 100.0,
            }
        )
        cls.assigned_move._action_assign()

        cls.assigned_production = cls.env["mrp.production"].create(
            {
                "product_id": cls.product.id,
                "reserved_lot_ids": [
                    fields.Command.set(cls.reserved_prod_lot.ids),
                ],
            }
        )

        cls.producing_production = cls.env["mrp.production"].create(
            {
                "product_id": cls.product.id,
                "lot_producing_id": cls.producing_lot.id,
            }
        )
