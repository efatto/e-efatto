from odoo import _, api, models
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.onchange("quantity_done")
    def _check_parallel_production(self):
        if (
            self.quantity_done
            and self.raw_material_production_id.is_parallel_production
        ):
            raise ValidationError(
                _(
                    "Changing quantity done for a production row in a "
                    "Parallel production is not allowed!\n Please set quantity "
                    "to consume to 0 before the end of the production and create "
                    "a new row with desired quantity."
                )
            )
