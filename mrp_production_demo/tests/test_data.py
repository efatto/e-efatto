# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common_data import TestProductionData


class TestData(TestProductionData):
    def test_update_product_qty(self):
        """Product quantity can be updated using the method in common tests."""
        # Arrange
        product = self.subproduct_1_1
        # pre-condition
        self.assertEqual(product.qty_available, 0)

        # Act
        self._update_product_qty(product, 5)

        # Assert
        self.assertEqual(product.qty_available, 5)
