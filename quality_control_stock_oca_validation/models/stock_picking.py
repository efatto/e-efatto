from odoo import _, models
from odoo.exceptions import ValidationError

from odoo.addons.quality_control_oca.models.qc_trigger_line import _filter_trigger_lines


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        for picking in self.sudo():
            # create new ispections on current configuration if needed
            inspection_model = self.env["qc.inspection"].sudo()
            qc_trigger = (
                self.env["qc.trigger"]
                .sudo()
                .search([("picking_type_id", "=", self.picking_type_id.id)])
            )
            for operation in self.move_lines:
                trigger_lines = set()
                for model in [
                    "qc.trigger.product_category_line",
                    "qc.trigger.product_template_line",
                    "qc.trigger.product_line",
                ]:
                    partner = (
                        self.partner_id if qc_trigger.partner_selectable else False
                    )
                    trigger_lines = trigger_lines.union(
                        self.env[model]
                        .sudo()
                        .get_trigger_line_for_product(
                            qc_trigger, operation.product_id.sudo(), partner=partner
                        )
                    )
                for trigger_line in _filter_trigger_lines(trigger_lines):
                    # this method does not duplicate existing inspections (behaviour
                    # added in this module
                    inspection = inspection_model._make_inspection(
                        operation, trigger_line
                    )
                    if inspection:
                        # force save of the new inspection, otherwise it will be deleted
                        inspection.env.cr.commit()
            for inspection in picking.qc_inspections_ids:
                if inspection.state not in ["success", "failed"] and (
                    inspection.object_id._name == "stock.move"  # noqa
                    and inspection.object_id.quantity_done > 0  # noqa
                    or inspection.object_id._name == "stock.move.line"  # noqa
                    and inspection.object_id.qty_done > 0  # noqa
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
        return super()._action_done()
