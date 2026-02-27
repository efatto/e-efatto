# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import Common


class TestLot(Common):
    def test_is_reserved_or_used(self):
        """
        Check that `is_reserved_or_used` is computed correctly.
        """
        # Arrange
        free_lot = self.free_lot
        reserved_move_lot = self.reserved_move_lot
        reserved_prod_lot = self.reserved_prod_lot
        producing_lot = self.producing_lot
        # Assert
        self.assertRecordValues(
            free_lot + reserved_move_lot + reserved_prod_lot + producing_lot,
            [
                {
                    "producing_production_ids": [],
                    "stock_move_line_ids": [],
                    "reserved_production_ids": [],
                },
                {
                    "producing_production_ids": [],
                    "stock_move_line_ids": self.assigned_move.move_line_ids.ids,
                    "reserved_production_ids": [],
                },
                {
                    "producing_production_ids": [],
                    "stock_move_line_ids": [],
                    "reserved_production_ids": self.assigned_production.ids,
                },
                {
                    "producing_production_ids": self.producing_production.ids,
                    "stock_move_line_ids": [],
                    "reserved_production_ids": [],
                },
            ],
        )
