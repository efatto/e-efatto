# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.tests import Form

from .common import Common


class TestSerialMatrix(Common):
    def _confirm_production(self):
        self.production.action_confirm()
        with Form(self.production) as production_form:
            with production_form.workorder_ids.edit(0) as workorder:
                workorder.duration = 15

    def test_00_validate(self):
        """
        When a serial production is produced with the matrix,
        the backorder productions are created as expected.
        """
        # Arrange
        production = self.production
        self._confirm_production()
        serial_matrix_wizard = self._init_matrix(production)
        # pre-condition
        self.assertTrue(production.is_parallel_production)
        self.assertTrue(production.workorder_ids.time_ids.duration, 15)

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
                    "product_id": self.serial_component.id,
                },
                {
                    "quantity_done": 2,
                    "product_id": self.component.id,
                },
                {
                    "quantity_done": 1,
                    "product_id": self.serial_component.id,
                },
                {
                    "quantity_done": 2,
                    "product_id": self.component.id,
                },
                {
                    "quantity_done": 1,
                    "product_id": self.serial_component.id,
                },
                {
                    "quantity_done": 2,
                    "product_id": self.component.id,
                },
            ],
        )

    def _todo_test_01_prepare(self):
        """
        When a serial production is prepared with the matrix,
        the backorder productions are prepared as expected.
        """
        # Arrange
        production = self.production
        self._confirm_production()
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
        Modify the quantity of components to:
        - component serial: untouched (3 total, 1 for each backorder)
        - component: from 6 to 12 total, 4 for each backorder instead of 2
          (they are split in 2 moves for 2 products each) IS FORBIDDEN!
        """
        # Arrange
        production = self.production
        self._confirm_production()
        component_move = production.move_raw_ids.filtered(
            lambda x: x.product_id == self.component
        )
        self.assertEqual(component_move.product_qty, 6)
        component_move_form = Form(
            component_move, view="mrp.view_stock_move_operations_raw"
        )
        with self.assertRaises(ValidationError):
            with component_move_form.move_line_ids.new() as ml_form:
                ml_form.qty_done = 12
        # component_move_form.save()
        # self.assertEqual(component_move.quantity_done, 12)
        # serial_matrix_wizard = self._init_matrix(production)
        # # pre-condition
        # self.assertTrue(production.is_parallel_production)
        # self.assertTrue(production.workorder_ids.time_ids.duration, 15)
        #
        # # Act
        # serial_matrix_wizard.button_validate()
        #
        # # Assert
        # parallel_production = production.parallel_production_id
        # parallel_productions = production.search(
        #     [
        #         ("parallel_production_id", "=", parallel_production.id),
        #     ]
        # )
        # self.assertRecordValues(
        #     parallel_productions.workorder_ids,
        #     [
        #         {
        #             "duration": 5,
        #         },
        #         {
        #             "duration": 5,
        #         },
        #         {
        #             "duration": 5,
        #         },
        #     ],
        # )
        # self.assertRecordValues(
        #     parallel_productions.move_raw_ids,
        #     [
        #         {
        #             "product_id": self.serial_component.id,
        #             "quantity_done": 1,
        #         },
        #         {
        #             "product_id": self.component.id,
        #             "quantity_done": 2,
        #         },
        #         {
        #             "product_id": self.component.id,
        #             "quantity_done": 2,
        #         },
        #         {
        #             "product_id": self.serial_component.id,
        #             "quantity_done": 1,
        #         },
        #         {
        #             "product_id": self.component.id,
        #             "quantity_done": 2,
        #         },
        #         {
        #             "product_id": self.component.id,
        #             "quantity_done": 2,
        #         },
        #         {
        #             "product_id": self.serial_component.id,
        #             "quantity_done": 1,
        #         },
        #         {
        #             "product_id": self.component.id,
        #             "quantity_done": 2,
        #         },
        #         {
        #             "product_id": self.component.id,
        #             "quantity_done": 2,
        #         },
        #     ],
        # )

    def _test_validate_removing_and_adding_component(self, confirmed=False):
        """
        Modify the quantity of components to:
            - serial component: untouched (3 total, 1 for each backorder)
            - component: from 6 to 0
        Adding:
            - new not tracked component: 9 total, 3 for each backorder
        """
        # Arrange
        production = self.production
        if confirmed:
            self._confirm_production()
        component_move = production.move_raw_ids.filtered(
            lambda x: x.product_id == self.component
        )
        self.assertEqual(component_move.product_qty, 6)
        if confirmed:
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
        if not confirmed:
            self._confirm_production()
        other_component_move = production.move_raw_ids.filtered(
            lambda x: x.product_id == self.other_component
        )
        production_form = Form(
            other_component_move, view="mrp.view_stock_move_operations_raw"
        )
        with production_form.move_line_ids.new() as ml_form:
            ml_form.qty_done = 9
        production_form.save()
        self.assertEqual(other_component_move.quantity_done, 9)
        serial_matrix_wizard = self._init_matrix(production)
        # pre-condition
        self.assertTrue(production.is_parallel_production)
        self.assertTrue(production.workorder_ids.time_ids.duration, 15)

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
                    "quantity_done": 3,
                },
                {
                    "product_id": self.serial_component.id,
                    "quantity_done": 1,
                },
                {
                    "product_id": self.other_component.id,
                    "quantity_done": 3,
                },
                {
                    "product_id": self.serial_component.id,
                    "quantity_done": 1,
                },
                {
                    "product_id": self.other_component.id,
                    "quantity_done": 3,
                },
            ],
        )

    def test_03_validate_removing_and_adding_component_draft(self):
        self._test_validate_removing_and_adding_component(confirmed=False)

    def test_03_validate_removing_and_adding_component_confirmed(self):
        self._test_validate_removing_and_adding_component(confirmed=True)
