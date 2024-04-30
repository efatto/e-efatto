from odoo import fields, models
from odoo.tools.date_utils import relativedelta


class QcTriggerProductLine(models.Model):
    _inherit = "qc.trigger.product_line"

    def get_trigger_line_for_product(self, trigger, product, partner=False):
        # get not active test too, to check if they need to be re-activated
        trigger_lines = super().get_trigger_line_for_product(
            trigger, product.with_context(active_test=False), partner=partner
        )
        inspection_model = self.env["qc.inspection"].sudo()
        # deactivate trigger line when success number of tests is reached
        for trigger_line in trigger_lines:
            if (
                not trigger_line.success_number_to_deactivation
                or not trigger_line.active
            ):
                continue
            inspections = inspection_model.search(
                [
                    ("product_id", "=", product.id),
                    ("test", "=", trigger_line.test.id),
                    ("state", "in", ["success", "failed"]),
                ],
                order="date desc",
                limit=trigger_line.success_number_to_deactivation,
            )
            if len(inspections) == trigger_line.success_number_to_deactivation and all(
                inspections.mapped("success")
            ):
                trigger_line.active = False
                # possible improvement: deactivate waiting checks
        # deactivate/activate trigger line when there are other inspection in the period
        for trigger_line in trigger_lines:
            if not trigger_line.trigger_activation_days:
                continue
            inspections = inspection_model.search(
                [
                    ("product_id", "=", product.id),
                    ("test", "=", trigger_line.test.id),
                    ("state", "in", ["success", "failed"]),
                    ("date", "<=", fields.Date.today()),
                    (
                        "date",
                        ">=",
                        fields.Date.today()
                        - relativedelta(days=trigger_line.trigger_activation_days),
                    ),
                ],
                order="date desc",
            )
            trigger_line.active = not bool(inspections)
            # possible improvement: deactivate waiting checks
        if trigger_lines:
            trigger_lines = [line for line in trigger_lines if line.active]
        return trigger_lines
