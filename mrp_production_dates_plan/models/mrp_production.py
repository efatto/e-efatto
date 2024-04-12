from odoo import api, models
from odoo.tools.date_utils import relativedelta


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _get_move_finished_values(
        self,
        product_id,
        product_uom_qty,
        product_uom,
        operation_id=False,
        byproduct_id=False,
    ):
        # ignore self.company_id.manufacturing_lead for date planned
        res = super()._get_move_finished_values(
            product_id,
            product_uom_qty,
            product_uom,
            operation_id=operation_id,
            byproduct_id=byproduct_id,
        )
        date_planned_finished = self.date_planned_start + relativedelta(
            days=self.product_id.produce_delay
        )
        if date_planned_finished == self.date_planned_start:
            date_planned_finished = date_planned_finished + relativedelta(hours=1)
        res["date"] = date_planned_finished
        return res

    @api.onchange("date_planned_start", "product_id", "date_planned_finished")
    def _onchange_date_planned_start(self):
        # ignore self.company_id.manufacturing_lead for date planned
        super()._onchange_date_planned_start()
        date_planned_finished = self.date_planned_start + relativedelta(
            days=self.product_id.produce_delay
        )
        if (
            self.date_planned_start
            and self.date_planned_finished != date_planned_finished
        ):
            if date_planned_finished == self.date_planned_start:
                date_planned_finished = date_planned_finished + relativedelta(hours=1)
            self.date_planned_finished = date_planned_finished
            self.move_finished_ids = [
                (1, m.id, {"date": date_planned_finished})
                for m in self.move_finished_ids
            ]
