# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import Common


class TestSerialMatrix(Common):
    def test_validate(self):
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

    def test_prepare(self):
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
