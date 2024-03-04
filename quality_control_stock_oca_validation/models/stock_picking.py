from odoo import _, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        if self.qc_inspections_ids:
            qc_inspection_todo_ids = self.qc_inspections_ids.filtered(
                lambda x: x.state not in ["success", "failed"]
            )
            if qc_inspection_todo_ids:
                raise ValidationError(
                    _(
                        "The stock picking cannot be validated as the following quality "
                        "control check are not completed: %s"
                    )
                    % ",".join(qc_inspection_todo_ids.mapped("name"))
                )
        return super()._action_done()
