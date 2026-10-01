from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_round


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"
    # _order = (
    #     "sequence ASC, date_start ASC, "
    #     "date_finished ASC"
    # )

    previous_work_order_ids = fields.Many2many(
        comodel_name="mrp.workorder",
        relation="mrp_workorder_previous_rel",
        column1="workorder_id",
        column2="previous_work_order_id",
        compute="_compute_previous_work_order_ids",
        store=True,
        help="Previous workorder of the current one",
    )
    origin = fields.Char(related="production_id.origin")
    to_be_replanned = fields.Boolean(
        compute="_compute_to_be_replanned",
        store=True,
        string="To be replanned or set to done.",
        help="Cases:\n 1. the estimated finished date has been overcome and the "
        "workorder is not 'in progress' or 'done' or 'cancelled'; 2. the planned "
        "start date has been overcome and the workorder is not 'in progress' or "
        "'done' or 'cancelled'; 3. the workorder is planned to be done in the "
        "same time of other workorders and is in state 'pending' or 'ready'.",
    )
    parallel_qty_production = fields.Float(
        string="Parallel Quantity",
        help="The quantity of the product to be produced in parallel with other "
        "workorders. The sum of all parallel production quantities must be equal "
        "to the production original quantity. This field is only used to compute "
        "the expected duration of the workorder.",
    )

    @api.depends("date_finished", "date_start", "state")
    def _compute_to_be_replanned(self):
        # todo 1: other logic depending on previous or next jobs?
        conflicted_dict = {}
        if self.ids:
            conflicted_dict = self._get_conflicted_workorder_ids()
        for wo in self:
            if (
                wo.date_finished
                and wo.date_finished < fields.Datetime.now()
                and wo.state not in ["progress", "done", "cancel"]
            ):
                wo.to_be_replanned = True
            elif (
                wo.date_start
                and wo.date_start < fields.Datetime.now()
                and wo.state not in ["progress", "done", "cancel"]
            ):
                wo.to_be_replanned = True
            elif conflicted_dict.get(wo.id):
                wo.to_be_replanned = True
            else:
                wo.to_be_replanned = False

    @api.depends(
        "production_id.workorder_ids.blocked_by_workorder_ids",
        "production_id.workorder_ids.operation_id.parallel_execution",
    )
    def _compute_previous_work_order_ids(self):
        for workorder in self:
            previous_work_order_ids = workorder.blocked_by_workorder_ids
            for operation_id in previous_work_order_ids.mapped("operation_id").filtered(
                "parallel_execution"
            ):
                previous_work_order_ids |= (
                    workorder.production_id.workorder_ids.filtered(
                        lambda w, op=operation_id: w.operation_id == op
                    )
                )
            parallel_workorders = workorder.production_id.workorder_ids.filtered(
                lambda wo, work=workorder: wo.operation_id == work.operation_id
            )
            previous_work_order_ids |= workorder.production_id.workorder_ids.filtered(
                lambda w, pw=parallel_workorders: w.blocked_by_workorder_ids in pw
            )
            workorder.previous_work_order_ids = previous_work_order_ids

    @api.depends("production_id.workorder_ids")
    def _compute_display_name(self):
        # call without super() as it is completely rewritten
        for wo in self:
            if len(wo.production_id.workorder_ids) == 1:
                wo.display_name = (
                    f"{wo.production_id.name} [{wo.product_id.default_code}] "
                    f"[qty {wo.production_id.product_qty}] {wo.name}"
                )
            else:
                wo.display_name = (
                    f"{wo.production_id.workorder_ids.ids.index(wo._origin.id) + 1}"
                    f" - {wo.production_id.name} "
                    f"[{wo.product_id.default_code}] "
                    f"[qty: {wo.production_id.product_qty}] "
                    f"{wo.name}",
                )

    def write(self, values):
        # Enable changing the duration of a workorder. It will change the end date of
        # the production if it's the last workorder (default behavior).
        initial_date_finished = self and self[0].date_finished
        production_to_replan = self.mapped("production_id").filtered(
            lambda p: p.is_planned
        )
        if "date_start" in values or "date_finished" in values:
            for workorder in self:
                start_date = fields.Datetime.to_datetime(
                    values.get("date_start", workorder.date_start)
                )
                end_date = fields.Datetime.to_datetime(
                    values.get("date_finished", workorder.date_finished)
                )
                if start_date and end_date and start_date > end_date:
                    raise UserError(
                        _(
                            "The planned end date of the work order cannot be prior to "
                            "the planned start date, please correct this to save the "
                            "work order."
                        )
                    )
                # part removed as duration_expected must be unchanged
                # todo without this code the user has some problems?
                # if start_date and end_date:
                #     computed_duration = workorder._calculate_duration_expected(
                #         date_start=start_date, date_finished=end_date
                #     )
                #     values["duration_expected"] = computed_duration
        res = super().write(values)
        if "parallel_qty_production" in values:
            # update after 'write'
            for workorder in self.filtered("parallel_qty_production"):
                if values.get("parallel_qty_production"):
                    workorder.duration_expected = workorder._get_duration_expected()
        if (
            initial_date_finished
            and not self.env.context.get("skip_move")
            and not self.env.context.get("force_date")
            and "leave_id" not in values
            and self
            and self[0].date_finished
        ):
            time_moved_finished = self[0].date_finished - initial_date_finished
            if time_moved_finished and production_to_replan:
                # this method replans only pending and ready workorders
                production_to_replan._plan_workorders(replan=True)
        return res

    def _get_duration_expected(self, alternative_workcenter=False, ratio=1):
        self.ensure_one()
        # if parallel execution is enabled and there is more than 1 optional workcenter,
        # split expected duration on workorders
        res = super()._get_duration_expected(
            alternative_workcenter=alternative_workcenter, ratio=ratio
        )
        if (
            (
                not self.parallel_qty_production
                and not self.env.context.get("parallel_qty_production")
            )
            and not self.workcenter_id
            or not self.operation_id
        ):
            return res
        qty_production = self.production_id.product_uom_id._compute_quantity(
            self.qty_production, self.production_id.product_id.uom_id
        )
        if self.env.context.get("parallel_qty_production"):
            qty_production = self.env.context.get("parallel_qty_production")
        elif self.parallel_qty_production:
            qty_production = self.parallel_qty_production
        cycle_number = qty_production / self.workcenter_id.default_capacity
        if alternative_workcenter:
            duration_expected_working = (
                (
                    self.duration_expected
                    - self.workcenter_id.time_start
                    - self.workcenter_id.time_stop
                )
                * self.workcenter_id.time_efficiency
                / (100.0 * cycle_number)
            )
            if duration_expected_working < 0:
                duration_expected_working = 0
            alternative_wc_cycle_nb = (
                qty_production / alternative_workcenter.default_capacity
            )
            return float_round(
                alternative_workcenter.time_start
                + alternative_workcenter.time_stop
                + alternative_wc_cycle_nb
                * duration_expected_working
                * 100.0
                / alternative_workcenter.time_efficiency,
                precision_digits=2,
                rounding_method="UP",
            )
        time_cycle = self.operation_id.time_cycle
        return float_round(
            self.workcenter_id.time_start
            + self.workcenter_id.time_stop
            + cycle_number * time_cycle * 100.0 / self.workcenter_id.time_efficiency,
            precision_digits=2,
            rounding_method="UP",
        )
