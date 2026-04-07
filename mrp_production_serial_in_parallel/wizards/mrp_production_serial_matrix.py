from dateutil.relativedelta import relativedelta

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tools import float_is_zero


class MrpProductionSerialMatrix(models.TransientModel):
    _inherit = "mrp.production.serial.matrix"

    @staticmethod
    def _split_work_time(production, backorder_ids):
        workorders_number = len(backorder_ids) + 1
        for time_id in production.workorder_ids.time_ids:
            # split times in workorders of backorders
            workorder = time_id.workorder_id
            new_duration = time_id.duration / workorders_number
            new_unit_amount = (
                time_id.unit_amount and (time_id.unit_amount / workorders_number) or 0
            )
            date_start = False
            for backorder in backorder_ids:
                back_workorder = backorder.workorder_ids.filtered(
                    lambda w: w.sequence == workorder.sequence
                    and w.name == workorder.name
                    and w.workcenter_id == workorder.workcenter_id
                )
                if not date_start:
                    date_start = time_id.date_start + relativedelta(
                        minutes=new_duration
                    )
                new_workorder_time = time_id.copy(
                    default={
                        "workorder_id": back_workorder.id,
                        "date_start": date_start,
                        "duration": new_duration,
                        "unit_amount": new_unit_amount,
                    }
                )
                new_workorder_time.duration = new_duration
                date_start = new_workorder_time.date_end
        for workorder_time in production.workorder_ids.time_ids:
            workorder_time.write(
                {
                    "duration": workorder_time.duration / workorders_number,
                    "unit_amount": workorder_time.unit_amount
                    and (workorder_time.unit_amount / workorders_number)
                    or 0,
                }
            )

    def _set_parallel_production(self):
        parallel_production = False
        if self.production_id.parallel_production_id:
            return self.production_id.parallel_production_id
        if self.production_id.is_parallel_production:
            # create a copy of current production and set as parallel production
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
        return parallel_production

    def _set_parallel_production_times(self, parallel_production=False):
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

    def _complete_consumption_wizard(self, res):
        consume_warning_form = Form(
            self.env["mrp.consumption.warning"].with_context(
                # bypass_check_state=True,   # todo verificare senza
                **res["context"]
            )
        )
        return consume_warning_form.save().action_confirm()

    def button_validate(self):
        self.ensure_one()
        # ensure no mess is coming from previous MOs writing 0 into producing qty
        self.production_id.qty_producing = 0
        self.production_id._onchange_product_qty()
        self.production_id._check_reserved_lot_qty()
        parallel_production = self._set_parallel_production()
        if self.lot_selection_warning_count > 0:
            raise UserError(
                _("Some issues has been detected in your selection: %s")
                % self.lot_selection_warning_msg
            )
        mos = self.env["mrp.production"]
        current_mo = self.production_id
        for fp_lot in self.finished_lot_ids:
            # Apply selected lots in matrix and set the qty producing
            current_mo.lot_producing_id = fp_lot
            current_mo.qty_producing = 1.0
            current_mo = current_mo.with_context(
                production_serial_matrix=True,
                first_production_serial_matrix=False,
            )
            if current_mo == self.production_id:
                # the first MO needs a different recomputation in quantities consumed
                current_mo = current_mo.with_context(
                    first_production_serial_matrix=True
                )
            current_mo._set_qty_producing()
            for move in current_mo.move_raw_ids:
                rounding = move.product_id.uom_id.rounding
                if float_is_zero(move.product_qty, precision_rounding=rounding):
                    # Component moves cannot be deleted in in-progress MO's; however,
                    # they can be set to 0 units to consume. In such case, we ignore
                    # the move.
                    continue
                if move.product_id.tracking in ["serial", "lot"]:
                    # We filter using the lot nane because the ORM sometimes
                    # is not storing correctly the finished_lot_id in the lines
                    # after passing through the `_onchange_finished_lot_ids`
                    # method.
                    matrix_lines = self.line_ids.filtered(
                        lambda l: (
                            l.finished_lot_id == fp_lot
                            or l.finished_lot_name == fp_lot.name
                        )
                        and l.component_id == move.product_id
                    )
                    if matrix_lines:
                        self._amend_reservations(move, matrix_lines)
                        self._consume_selected_lots(move, matrix_lines)

            # Complete MO and create backorder if needed.
            mos += current_mo
            res = current_mo.button_mark_done()
            if isinstance(res, dict) and res.get("context"):
                res["context"].update(
                    production_serial_matrix=True,
                )
            # default backorder's wizard creates mos from selected bom, ignoring changes
            # done by the user
            backorder_wizard = self.env["mrp.production.backorder"].with_context(
                backorder_serial_matrix=True
            )
            if (
                isinstance(res, dict)
                and res.get("res_model") == "mrp.consumption.warning"
            ):
                res = self._complete_consumption_wizard(res)
            if isinstance(res, dict) and res.get("res_model") == backorder_wizard._name:
                # create backorders...
                lines = res.get("context", {}).get(
                    "default_mrp_production_backorder_line_ids"
                )
                wizard = backorder_wizard.create(
                    {
                        "mrp_production_ids": current_mo.ids,
                        "mrp_production_backorder_line_ids": lines,
                    }
                )
                res = wizard.action_backorder()
                if (
                    isinstance(res, dict)
                    and res.get("res_model") == "mrp.consumption.warning"
                ):
                    res["context"].update(
                        production_serial_matrix=True,
                    )
                    self._complete_consumption_wizard(res)
                backorder_ids = (
                    current_mo.procurement_group_id.mrp_production_ids.filtered(
                        lambda mo: mo.state not in ["done", "cancel"]
                    )
                )
                current_mo = backorder_ids[0] if backorder_ids else False
                if not current_mo:
                    break
                current_mo.parallel_production_id = parallel_production
            else:
                break

        # TODO: not specified lots: auto create lots?
        if not mos:
            mos = self.production_id
        res = {
            "domain": [("id", "in", mos.ids)],
            "name": _("Manufacturing Orders"),
            "src_model": "mrp.production.serial.matrix",
            "view_type": "form",
            "view_mode": "tree,form",
            "view_id": False,
            "views": False,
            "res_model": "mrp.production",
            "type": "ir.actions.act_window",
        }
        if parallel_production:
            self._set_parallel_production_times(parallel_production)
        return res

    def button_prepare(self):
        self.ensure_one()
        # ensure no mess is coming from previous MOs writing 0 into producing qty
        self.production_id.qty_producing = 0
        self.production_id._onchange_product_qty()
        self.production_id._check_reserved_lot_qty()
        parallel_production = self._set_parallel_production()
        if self.lot_selection_warning_count > 0:
            raise UserError(
                _("Some issues has been detected in your selection: %s")
                % self.lot_selection_warning_msg
            )
        mos = self.env["mrp.production"]
        current_mo = self.production_id
        for fp_lot in self.finished_lot_ids:
            # Apply selected lots in matrix and set the qty producing
            current_mo.lot_producing_id = fp_lot
            current_mo.qty_producing = 1.0
            current_mo._set_qty_producing()
            for move in current_mo.move_raw_ids:
                rounding = move.product_id.uom_id.rounding
                if float_is_zero(move.product_qty, precision_rounding=rounding):
                    # Component moves cannot be deleted in in-progress MO's; however,
                    # they can be set to 0 units to consume. In such case, we ignore
                    # the move.
                    continue
                if move.product_id.tracking in ["serial", "lot"]:
                    # We filter using the lot nane because the ORM sometimes
                    # is not storing correctly the finished_lot_id in the lines
                    # after passing through the `_onchange_finished_lot_ids`
                    # method.
                    matrix_lines = self.line_ids.filtered(
                        lambda l: (
                            l.finished_lot_id == fp_lot
                            or l.finished_lot_name == fp_lot.name
                        )
                        and l.component_id == move.product_id
                    )
                    if matrix_lines:
                        self._amend_reservations(move, matrix_lines)
                        self._consume_selected_lots(move, matrix_lines)

            # Complete MO and create backorder if needed.
            mos += current_mo
            backorders = False
            if current_mo.product_qty > 1:
                backorders = current_mo._generate_backorder_productions(close_mo=False)
                current_mo.write({"product_qty": current_mo.qty_producing})
            if backorders:
                current_mo = backorders[0]
                current_mo.write({"parallel_production_id": parallel_production.id})
            else:
                break

        # TODO: not specified lots: auto create lots?
        if not mos:
            mos = self.production_id
        res = {
            "domain": [("id", "in", mos.ids)],
            "name": _("Manufacturing Orders"),
            "binding_model_id": self.env["ir.model.data"].xmlid_to_res_id(
                "mrp_production_serial_matrix.model_mrp_production_serial_matrix"
            ),
            "view_mode": "tree,form",
            "view_id": False,
            "views": False,
            "res_model": "mrp.production",
            "type": "ir.actions.act_window",
        }
        return res
