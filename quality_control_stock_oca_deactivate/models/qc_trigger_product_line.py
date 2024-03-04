from odoo import models


class QcTriggerProductLine(models.Model):
    _inherit = "qc.trigger.product_line"

    def get_trigger_line_for_product(self, trigger, product, partner=False):
        trigger_lines = super().get_trigger_line_for_product(
            trigger, product, partner=partner
        )
        # deactivate trigger line when success number of tests is reached
        for trigger_line in trigger_lines:
            inspections = self.env["qc.inspection"].search(
                [
                    ("product_id", "=", product.id),
                    ("test", "=", trigger_line.test.id),
                ],
                order="date desc",
                limit=trigger_line.success_number_to_deactivation,
            )
            if len(inspections) == trigger_line.success_number_to_deactivation and all(
                inspections.mapped("success")
            ):
                trigger_line.active = False
                # todo disattivare anche i controlli in attesa?
        if trigger_lines:
            trigger_lines = [line for line in trigger_lines if line.active]
        return trigger_lines
