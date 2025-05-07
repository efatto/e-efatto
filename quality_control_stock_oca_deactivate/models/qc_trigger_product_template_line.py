from odoo import fields, models
from odoo.tools.date_utils import relativedelta


class QcTriggerProductTemplateLine(models.Model):
    _inherit = "qc.trigger.product_template_line"

    def get_trigger_line_for_product(self, trigger, product, partner=False):
        # get not active test too, to check if they need to be re-activated
        trigger_lines = super().get_trigger_line_for_product(
            trigger, product.with_context(active_test=False), partner=partner
        )
        inspection_obj = self.env["qc.inspection"].sudo()
        # deactivate trigger line when success number of tests is reached
        for trigger_line in trigger_lines:
            if (
                not trigger_line.success_number_to_deactivation
                or not trigger_line.active
            ):
                continue
            inspections = inspection_obj.search(
                [
                    ("product_id", "=", product.id),
                    ("test", "=", trigger_line.test.id),
                    ("state", "in", ["success", "failed"]),
                ],
                order="date desc",
                limit=trigger_line.success_number_to_deactivation,
            )
            if len(inspections) == trigger_line.success_number_to_deactivation and all(
                ins.state == "success" for ins in inspections
            ):
                trigger_line.active = False
        # deactivate/activate trigger line when there are other inspection in the period
        for trigger_line in trigger_lines:
            if trigger_line.trigger_activation_days:
                inspections = inspection_obj.search(
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
        # activate/deactivate trigger line if trigger_activation_number is reached/not
        # reached
        for trigger_line in trigger_lines:
            if trigger_line.trigger_activation_number:
                # todo activate inspection if there are more then activation number
                #  not-created inspection
                inspected_pickings = (
                    self.env["stock.picking"]
                    .sudo()
                    .search(
                        [
                            ("picking_type_id", "=", trigger.picking_type_id.id),
                            ("move_lines.product_id", "=", product.id),
                            ("qc_inspections_ids", "!=", False),
                        ],
                        order="date desc",
                        limit=1,
                    )
                )
                if inspected_pickings:
                    not_inspected_pickings = (
                        self.env["stock.picking"]
                        .sudo()
                        .search(
                            [
                                ("picking_type_id", "=", trigger.picking_type_id.id),
                                ("move_lines.product_id", "=", product.id),
                                ("qc_inspections_ids", "=", False),
                                ("id", "not in", inspected_pickings.ids),
                                ("date", ">=", inspected_pickings.date),
                            ]
                        )
                    )
                    if (
                        len(not_inspected_pickings)
                        >= trigger_line.trigger_activation_number
                    ):
                        trigger_line.active = not bool(trigger_line.active)
        if trigger_lines:
            trigger_lines = [line for line in trigger_lines if line.active]
        return trigger_lines
