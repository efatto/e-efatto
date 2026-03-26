# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form

from .common import Common


class TestSerialMatrix(Common):
    def test_00_validate(self):
        """
        When a serial production is produced with the matrix,
        the backorder productions are created as expected.
        """
        # Arrange
        production = self.production
        serial_matrix_wizard = self._init_matrix(production)
        # pre-condition
        self.assertTrue(production.is_parallel_production)
        self.assertTrue(production.workorder_ids.time_ids.duration, 10)

        # Act
        serial_matrix_wizard.button_validate()

        # Assert
        parallel_production = production.parallel_production_id
        parallel_productions = production.search(
            [
                ("parallel_production_id", "=", parallel_production.id),
            ]
        )
        self.assertRecordValues(
            parallel_productions.workorder_ids,
            [
                {
                    "duration": 5,
                },
                {
                    "duration": 5,
                },
            ],
        )
        self.assertRecordValues(
            parallel_productions.move_raw_ids,
            [
                {
                    "quantity_done": 1,
                },
                {
                    "quantity_done": 2,
                },
                {
                    "quantity_done": 1,
                },
                {
                    "quantity_done": 2,
                },
            ],
        )

    def test_01_prepare(self):
        """
        When a serial production is prepared with the matrix,
        the backorder productions are prepared as expected.
        """
        # Arrange
        production = self.production
        serial_matrix_wizard = self._init_matrix(production)
        # pre-condition
        self.assertTrue(production.is_parallel_production)

        # Act
        prepared_mos_action = serial_matrix_wizard.button_prepare()

        # Assert
        prepared_mos = self._get_records_from_action(prepared_mos_action)
        parallel_production = prepared_mos.parallel_production_id
        parallel_productions = production.search(
            [
                ("parallel_production_id", "=", parallel_production.id),
            ]
        )
        self.assertEqual(prepared_mos, parallel_productions)

    def test_02_validate_changing_qty_done(self):
        """
        When a serial production is produced with the matrix with consumption warnings,
        the backorder productions are created as expected.
        """
        # Arrange
        production = self.production
        component_move = production.move_raw_ids.filtered(
            lambda x: x.product_id == self.component
        )
        self.assertEqual(component_move.product_qty, 4)
        component_move_form = Form(
            component_move, view="mrp.view_stock_move_operations_raw"
        )
        with component_move_form.move_line_ids.new() as ml_form:
            ml_form.qty_done = 10
        component_move_form.save()
        self.assertEqual(component_move.quantity_done, 10)
        serial_matrix_wizard = self._init_matrix(production)
        # pre-condition
        self.assertTrue(production.is_parallel_production)
        self.assertTrue(production.workorder_ids.time_ids.duration, 10)

        # Act
        serial_matrix_wizard.button_validate()

        # Assert
        parallel_production = production.parallel_production_id
        parallel_productions = production.search(
            [
                ("parallel_production_id", "=", parallel_production.id),
            ]
        )
        self.assertRecordValues(
            parallel_productions.workorder_ids,
            [
                {
                    "duration": 5,
                },
                {
                    "duration": 5,
                },
            ],
        )
        self.assertRecordValues(
            parallel_productions.move_raw_ids,
            [
                {
                    "product_id": self.serial_component.id,
                    "quantity_done": 1,
                },
                {
                    "product_id": self.component.id,
                    "quantity_done": 2,
                },
                {
                    "product_id": self.component.id,
                    "quantity_done": 3,
                },
                {
                    "product_id": self.serial_component.id,
                    "quantity_done": 1,
                },
                {
                    "product_id": self.component.id,
                    "quantity_done": 2,
                },
                {
                    "product_id": self.component.id,
                    "quantity_done": 3,
                },
            ],
        )

    def test_03_validate_removing_and_adding_component(self):
        """
        When a serial production is produced with the matrix with consumption warnings,
        the backorder productions are created as expected.
        """
        # Arrange
        production = self.production
        component_move = production.move_raw_ids.filtered(
            lambda x: x.product_id == self.component
        )
        self.assertEqual(component_move.product_qty, 4)
        if production.is_locked:
            production.action_toggle_is_locked()
        self.assertFalse(production.is_locked)
        production_form = Form(production)
        with production_form.move_raw_ids.edit(1) as m_form:
            m_form.product_uom_qty = 0
        production = production_form.save()
        self.assertEqual(
            production.move_raw_ids.filtered(
                lambda x: x.product_id == self.component
            ).product_uom_qty,
            0,
        )
        production_form = Form(production)
        with production_form.move_raw_ids.new() as move_form:
            move_form.product_id = self.other_component
        production_form.save()
        other_component_move = production.move_raw_ids.filtered(
            lambda x: x.product_id == self.other_component
        )
        production_form = Form(
            other_component_move, view="mrp.view_stock_move_operations_raw"
        )
        with production_form.move_line_ids.new() as ml_form:
            ml_form.qty_done = 8
        production_form.save()
        self.assertEqual(other_component_move.quantity_done, 8)
        serial_matrix_wizard = self._init_matrix(production)
        # pre-condition
        self.assertTrue(production.is_parallel_production)
        self.assertTrue(production.workorder_ids.time_ids.duration, 10)

        # Act
        serial_matrix_wizard.button_validate()

        # Assert
        parallel_production = production.parallel_production_id
        parallel_productions = production.search(
            [
                ("parallel_production_id", "=", parallel_production.id),
            ]
        )
        self.assertRecordValues(
            parallel_productions.workorder_ids,
            [
                {
                    "duration": 5,
                },
                {
                    "duration": 5,
                },
            ],
        )
        self.assertRecordValues(
            parallel_productions.move_raw_ids,
            [
                {
                    "product_id": self.serial_component.id,
                    "quantity_done": 1,
                },
                {
                    "product_id": self.component.id,
                    "quantity_done": 0,
                },
                {
                    "product_id": self.other_component.id,
                    "quantity_done": 4,
                },
                {
                    "product_id": self.serial_component.id,
                    "quantity_done": 1,
                },
                {
                    "product_id": self.other_component.id,
                    "quantity_done": 4,
                },
            ],
        )
