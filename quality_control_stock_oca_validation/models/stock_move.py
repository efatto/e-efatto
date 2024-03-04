from odoo import api, models

from odoo.addons.quality_control_oca.models.qc_trigger_line import _filter_trigger_lines


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_confirm(self, merge=True, merge_into=False):
        self.create_qc_inspection()
        return super()._action_confirm(merge, merge_into)

    @api.model
    def create_qc_inspection(self):
        inspection_model = self.env["qc.inspection"].sudo()
        for operation in self:
            qc_trigger = (
                self.env["qc.trigger"]
                .sudo()
                .search(
                    [("picking_type_id", "=", operation.picking_id.picking_type_id.id)]
                )
            )
            trigger_lines = set()
            for model in [
                "qc.trigger.product_category_line",
                "qc.trigger.product_template_line",
                "qc.trigger.product_line",
            ]:
                partner = (
                    operation.picking_id.partner_id
                    if (qc_trigger.partner_selectable)
                    else False
                )
                trigger_lines = trigger_lines.union(
                    self.env[model]
                    .sudo()
                    .get_trigger_line_for_product(
                        qc_trigger, operation.product_id.sudo(), partner=partner
                    )
                )
            for trigger_line in _filter_trigger_lines(trigger_lines):
                inspection_model._make_inspection(operation, trigger_line)
