# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import Common


class TestSerialMatrix(Common):
    def test_default_lots(self):
        """
        Check that default selected lots for the serial matrix
        come from the production.
        """
        # Arrange
        production = self.assigned_production
        reserved_lots = production.reserved_lot_ids

        # Act
        serial_matrix_wizard = (
            self.env["mrp.production.serial.matrix"]
            .with_context(
                active_model=production._name,
                active_id=production.id,
            )
            .create({})
        )

        # Assert
        self.assertRecordValues(
            serial_matrix_wizard,
            [
                {
                    "finished_lot_ids": reserved_lots.ids,
                },
            ],
        )
