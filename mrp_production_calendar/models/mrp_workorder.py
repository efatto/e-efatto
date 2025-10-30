from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_round


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"
    _order = (
        "sequence ASC, next_work_order_id DESC, date_planned_start ASC, "
        "date_planned_finished ASC"
    )

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

    @api.depends("date_planned_finished", "date_planned_start", "state")
    def _compute_to_be_replanned(self):
        # todo 1: other logic depending on previous or next jobs?
        conflicted_dict = {}
        if self.ids:
            conflicted_dict = self._get_conflicted_workorder_ids()
        for wo in self:
            if (
                wo.date_planned_finished
                and wo.date_planned_finished < fields.Datetime.now()
                and wo.state not in ["progress", "done", "cancel"]
            ):
                wo.to_be_replanned = True
            elif (
                wo.date_planned_start
                and wo.date_planned_start < fields.Datetime.now()
                and wo.state not in ["progress", "done", "cancel"]
            ):
                wo.to_be_replanned = True
            elif conflicted_dict.get(wo.id):
                wo.to_be_replanned = True
            else:
                wo.to_be_replanned = False

    @api.depends(
        "production_id.workorder_ids.next_work_order_id",
        "production_id.workorder_ids.operation_id.parallel_execution",
    )
    def _compute_previous_work_order_ids(self):
        for workorder in self:
            previous_work_order_ids = workorder.production_id.workorder_ids.filtered(
                lambda w: w.next_work_order_id == workorder
            )
            for operation_id in previous_work_order_ids.mapped("operation_id").filtered(
                "parallel_execution"
            ):
                previous_work_order_ids |= (
                    workorder.production_id.workorder_ids.filtered(
                        lambda w: w.operation_id == operation_id
                    )
                )
            parallel_workorders = workorder.production_id.workorder_ids.filtered(
                lambda wo: wo.operation_id == workorder.operation_id
            )
            previous_work_order_ids |= workorder.production_id.workorder_ids.filtered(
                lambda w: w.next_work_order_id in parallel_workorders
            )
            workorder.previous_work_order_ids = previous_work_order_ids

    def name_get(self):
        # call without super() as it is completely rewritten
        res = []
        for wo in self:
            if len(wo.production_id.workorder_ids) == 1:
                res.append(
                    (
                        wo.id,
                        "%s [%s] [qty %s] %s"
                        % (
                            wo.production_id.name,
                            wo.product_id.default_code,
                            wo.production_id.product_qty,
                            wo.name,
                        ),
                    )
                )
            else:
                res.append(
                    (
                        wo.id,
                        "%s - %s [%s] [qty: %s] %s"
                        % (
                            wo.production_id.workorder_ids.ids.index(wo._origin.id) + 1,
                            wo.production_id.name,
                            wo.product_id.default_code,
                            wo.production_id.product_qty,
                            wo.name,
                        ),
                    )
                )
        return res

    def _move_workorder(self, time_moved):
        workorders_tobe_moved = self.env["mrp.workorder"].browse()
        for workcenter in self.mapped("workcenter_id"):
            # dates in mo are used to replan, so we simply "move" the workorders for
            # the moved time, instead of doing a complete replanning
            workorders_tobe_moved |= self.env["mrp.workorder"].search(
                [
                    ("workcenter_id", "=", workcenter.id),
                    ("state", "in", ["pending", "ready"]),
                    ("date_planned_start", ">=", self.date_planned_start),
                    ("date_planned_finished", "!=", False),
                    ("id", "!=", self.id),
                ]
            )
            workorders_tobe_moved |= self.env["mrp.workorder"].search(
                [
                    ("previous_work_order_ids", "in", self.ids),
                    ("date_planned_start", "!=", False),
                ]
            )
        for workorder in workorders_tobe_moved:
            workorder.with_context(skip_move=True).write(
                {
                    "date_planned_start": workorder.date_planned_start + time_moved,
                    "date_planned_finished": workorder.date_planned_finished
                    + time_moved,
                }
            )
        # TODO do not replan, check if the method can be used
        # for production in workorders_tobe_moved.mapped("production_id"):
        #     production.with_context(skip_move=True)._plan_workorders(replan=True)
        #     # We replan children workorders too, as we call this action at
        #     # mrp.production level (btw, even calling from mrp.workorder to
        #     # the same, but we call directly from the production to minimize
        #     # method calls
        # todo check if workorders in other workcenters which were planned
        #  after these ones are replanned correctly, to avoid holes in
        #  workcenter planners

    def write(self, values):
        # Enable changing the duration of a workorder. It will change the end date of
        # the production if it's the last workorder (default behavior).
        initial_date_planned_finished = self and self[0].date_planned_finished
        if "date_planned_start" in values or "date_planned_finished" in values:
            for workorder in self:
                start_date = fields.Datetime.to_datetime(
                    values.get("date_planned_start", workorder.date_planned_start)
                )
                end_date = fields.Datetime.to_datetime(
                    values.get("date_planned_finished", workorder.date_planned_finished)
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
                #         date_planned_start=start_date, date_planned_finished=end_date
                #     )
                #     values["duration_expected"] = computed_duration
        res = super().write(values)
        if "parallel_qty_production" in values:
            # update after 'write'
            for workorder in self.filtered("parallel_qty_production"):
                if values.get("parallel_qty_production"):
                    workorder.duration_expected = workorder._get_duration_expected()
        if (
            initial_date_planned_finished
            and not self.env.context.get("skip_move")
            and self
            and self[0].date_planned_finished
        ):
            time_moved_finished = (
                self[0].date_planned_finished - initial_date_planned_finished
            )
            if time_moved_finished:
                self._move_workorder(time_moved_finished)
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
        cycle_number = qty_production / self.workcenter_id.capacity
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
            alternative_wc_cycle_nb = qty_production / alternative_workcenter.capacity
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
