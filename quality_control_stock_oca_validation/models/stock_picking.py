from odoo import _, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        for picking in self:
            for inspection in picking.qc_inspections_ids:
                if (
                    inspection.object_id._name == "stock.move"
                    and inspection.object_id.quantity_done > 0
                    and inspection.state not in ["success", "failed"]
                ):
                    raise ValidationError(
                        _(
                            "The stock picking cannot be validated as the following "
                            "quality control check are not completed: %s"
                        )
                        % inspection.name
                    )
        return super()._action_done()
