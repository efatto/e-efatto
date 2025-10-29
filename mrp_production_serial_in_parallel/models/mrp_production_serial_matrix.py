from dateutil.relativedelta import relativedelta

from odoo import models


class MrpProductionSerialMatrix(models.TransientModel):
    _inherit = "mrp.production.serial.matrix"

    @staticmethod
    def _split_work_time(production, backorder_ids):
        for backorder in backorder_ids:
            for workorder in production.workorder_ids:
                if workorder.time_ids:
                    back_workorder = backorder.workorder_ids.filtered(
                        lambda w: w.sequence == workorder.sequence
                        and w.name == workorder.name
                        and w.workcenter_id == workorder.workcenter_id
                    )
                    date_start = False
                    for workorder_time in workorder.time_ids:  # todo check sort!
                        new_duration = workorder_time.duration / (
                            len(backorder_ids) + 1
                        )
                        if not date_start or workorder_time == workorder.time_ids[0]:
                            date_start = workorder_time.date_start + relativedelta(
                                minutes=new_duration
                            )
                            # todo usare un calcolatore di tempo dalle risorse? o è
                            #  inutile essendo che sono tempi sempre all'interno di
                            #  un orario di lavoro?
                        new_workorder_time = workorder_time.copy(
                            default={
                                "workorder_id": back_workorder.id,
                                "date_start": date_start,
                                "duration": new_duration,
                            }
                        )
                        date_start = new_workorder_time.date_end
        for workorder_time in production.workorder_ids.time_ids:
            workorder_time.write(
                {
                    "duration": workorder_time.duration / (len(backorder_ids) + 1),
                }
            )
        return False

    def button_validate(self):
        self.ensure_one()
        self.production_id._check_reserved_lot_qty()
        parallel_production = False
        if self.production_id.is_parallel_production:
            parallel_production = self.production_id.copy(
                default={
                    "name": "%s - serial in parallel" % self.production_id.name,
                    "reserved_lot_ids": [
                        (4, lot.id) for lot in self.production_id.reserved_lot_ids
                    ],
                }
            )
            parallel_production.action_cancel()
            parallel_production.write({"procurement_group_id": False})
            self.production_id.write(
                {
                    "parallel_production_id": parallel_production.id,
                    "reserved_lot_ids": [(5,)],
                }
            )
        res = super().button_validate()
        if parallel_production:
            # parallel production is a copy without work times, the production with
            # work times is the self.production_id, which is in the backorders too
            backorder_ids = (
                self.production_id.procurement_group_id.mrp_production_ids.filtered(
                    lambda mo: mo.state != "cancel"
                )
            )
            backorder_ids.write({"parallel_production_id": parallel_production.id})
            if self.production_id.workorder_ids.time_ids:
                self._split_work_time(
                    self.production_id, backorder_ids - self.production_id
                )
        return res
