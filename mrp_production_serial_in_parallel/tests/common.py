# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import tests
from odoo.tests.common import SavepointCase


class Common(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.component = cls.env["product.product"].create(
            {
                "name": "Test Component",
                "type": "product",
                "tracking": "none",
            }
        )
        cls.env["stock.quant"].create(
            [
                {
                    "product_id": cls.component.id,
                    "location_id": cls.stock_location.id,
                    "quantity": 15,
                }
            ]
        )
        cls.other_component = cls.env["product.product"].create(
            {
                "name": "Test Other Component",
                "type": "product",
                "tracking": "none",
            }
        )
        cls.env["stock.quant"].create(
            [
                {
                    "product_id": cls.other_component.id,
                    "location_id": cls.stock_location.id,
                    "quantity": 15,
                }
            ]
        )
        cls.serial_product = cls.env["product.product"].create(
            {
                "name": "Test Serial Product",
                "type": "product",
                "tracking": "serial",
            }
        )
        cls.product_serials = cls.env["stock.production.lot"].create(
            [
                {
                    "name": f"Test Serial {index} for Product",
                    "product_id": cls.serial_product.id,
                }
                for index in range(3)
            ]
        )
        cls.serial_component = cls.env["product.product"].create(
            {
                "name": "Test Serial Component",
                "type": "product",
                "tracking": "serial",
            }
        )
        cls.component_serials = cls.env["stock.production.lot"].create(
            [
                {
                    "name": f"Test Serial {index} for Component",
                    "product_id": cls.serial_component.id,
                }
                for index in range(3)
            ]
        )
        cls.env["stock.quant"].create(
            [
                {
                    "product_id": component_serial.product_id.id,
                    "lot_id": component_serial.id,
                    "location_id": cls.stock_location.id,
                    "quantity": 1,
                }
                for component_serial in cls.component_serials
            ]
        )

        cls.workcenter = cls.env["mrp.workcenter"].create(
            {
                "name": "Test workcenter",
            }
        )

        bom_form = tests.Form(cls.env["mrp.bom"])
        bom_form.product_tmpl_id = cls.serial_product.product_tmpl_id
        bom_form.product_id = cls.serial_product
        with bom_form.bom_line_ids.new() as line:
            line.product_id = cls.serial_component
        with bom_form.bom_line_ids.new() as line:
            line.product_id = cls.component
            line.product_qty = 2
        with bom_form.operation_ids.new() as operation:
            operation.name = "Test operation"
            operation.workcenter_id = cls.workcenter
        cls.bom = bom_form.save()

        production_form = tests.Form(cls.env["mrp.production"])
        production_form.product_id = cls.serial_product
        production_form.product_qty = 3
        cls.production = production_form.save()
        cls.production.write({"reserved_lot_ids": [(6, 0, cls.product_serials.ids)]})

    @classmethod
    def _init_matrix(cls, production):
        serial_matrix_wizard = (
            cls.env["mrp.production.serial.matrix"]
            .with_context(
                active_model=production._name,
                active_id=production.id,
            )
            .create({})
        )

        for line_index, line in enumerate(serial_matrix_wizard.line_ids):
            line.finished_lot_id = production.reserved_lot_ids[line_index]
            line.component_lot_id = cls.component_serials[line_index]
        return serial_matrix_wizard

    @classmethod
    def _get_records_from_action(cls, action):
        return cls.env[action["res_model"]].search(action["domain"])
