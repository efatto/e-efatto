from odoo import _, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        for picking in self.sudo():
            for inspection in picking.qc_inspections_ids:
                if inspection.state not in ["success", "failed"] and (
                    inspection.object_id.quantity > 0
                ):
                    raise ValidationError(
                        _(
                            "The stock picking cannot be validated as the following "
                            "quality control check are not completed: %s"
                            "\n(Refresh the page if quality control is not visible, as "
                            "it may have been created now)"
                        )
                        % inspection.name
                    )
        res = super()._action_done()
        # fix picking_id linked to inspection if it is no more linked to the same
        # picking, after _action_done execution
        for picking in self.sudo():
            for inspection in picking.qc_inspections_ids:
                if (
                    inspection.object_id._name in ["stock.move", "stock.move.line"]
                    and inspection.object_id.picking_id != picking
                ):
                    inspection.picking_id = inspection.object_id.picking_id
        return res

    def write(self, vals):
        res = super().write(vals)
        if vals.get("dn_supplier_number") or vals.get("dn_supplier_date"):  # noqa
            draft_inspections = self.qc_inspections_ids.filtered(
                lambda i: i.state == "draft"
            )
            draft_inspections.action_todo()
        return res
