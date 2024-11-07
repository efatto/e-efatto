# Copyright 2023 Sergio Corato
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context


class ProductReplenish(models.TransientModel):
    _inherit = "product.replenish"

    def launch_replenishment_with_origin(self):
        # replace original method launch_replenishment to set origin from context
        uom_reference = self.product_id.uom_id
        self.quantity = self.product_uom_id._compute_quantity(
            self.quantity, uom_reference
        )
        try:
            self.env["procurement.group"].with_context(
                clean_context(self.env.context)
            ).run(
                [
                    self.env["procurement.group"].Procurement(
                        self.product_id,
                        self.quantity,
                        uom_reference,
                        self.warehouse_id.lot_stock_id,  # Location
                        _("Manual Replenishment"),  # Name
                        self.env.context.get(
                            "origin", _("Manual Replenishment")
                        ),  # Origin
                        self.warehouse_id.company_id,
                        self._prepare_run_values(),  # Values
                    )
                ]
            )
        except UserError as error:
            raise UserError(error)
