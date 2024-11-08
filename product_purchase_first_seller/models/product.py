# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _select_seller(
        self, partner_id=False, quantity=0.0, date=None, uom_id=False, params=False
    ):
        res = super()._select_seller(partner_id, quantity, date, uom_id, params)
        sellers = self._prepare_sellers()
        if sellers:
            if res.name != sellers[0].name:
                res = sellers[0]
        return res
