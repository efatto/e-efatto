from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class MrpProductionSerialMatrix(models.TransientModel):
    _inherit = "mrp.production.serial.matrix"

    @staticmethod
    def _split_work_time(production, backorder_ids):
        def match_workorder(original_wo, available_wos):
            """
            Find which workorder in `available_wos` corresponds to `original_wo`.

            Corresponding workorders will have the same registered time.
            """
            return available_wos.filtered(
                lambda available_wo, original_wo=original_wo: (
                    available_wo.sequence == original_wo.sequence
                    and available_wo.name == original_wo.name
                    and available_wo.workcenter_id == original_wo.workcenter_id
                )
            )

        # Remove default backorder times for involved workcenters
        to_reset_workorders = production.workorder_ids.browse()
        for time_id in production.workorder_ids.time_ids:
            to_reset_workorders |= match_workorder(
                time_id.workorder_id, backorder_ids.workorder_ids
            )
        if to_reset_workorders.time_ids:
            to_reset_workorders.time_ids.unlink()

        # Split times in workorders of backorders
        workorders_number = len(backorder_ids) + 1
        for time_id in production.workorder_ids.time_ids:
            workorder = time_id.workorder_id
            new_duration = time_id.duration / workorders_number
            new_unit_amount = (
                time_id.unit_amount and (time_id.unit_amount / workorders_number) or 0
            )
            date_start = False
            for backorder in backorder_ids:
                back_workorder = match_workorder(workorder, backorder.workorder_ids)
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
                date_start = new_workorder_time.date_end

        # Adjust time of original production that has become a backorder
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
        if self.production_id.is_parallel_production:
            parallel_production = self.production_id.copy(
                default={
                    "name": f"{self.production_id.name} - serial in parallel",
                    "reserved_lot_ids": [
                        fields.Command.link(lot.id)
                        for lot in self.production_id.reserved_lot_ids
                    ],
                }
            )
            parallel_production.action_cancel()
            parallel_production.write({"procurement_group_id": False})
            self.production_id.write(
                {
                    "parallel_production_id": parallel_production.id,
                    "reserved_lot_ids": [fields.Command.clear()],
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

    def button_validate(self):
        self.ensure_one()
        self.production_id._check_reserved_lot_qty()
        parallel_production = self._set_parallel_production()
        res = super().button_validate()
        if parallel_production:
            self._set_parallel_production_times(parallel_production)
        return res

    def button_prepare(self):
        self.ensure_one()
        self.production_id._check_reserved_lot_qty()
        parallel_production = self._set_parallel_production()
        # Start copy/paste from super's button_validate
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
                        lambda line: (
                            line.finished_lot_id == fp_lot  # noqa: B023
                            or line.finished_lot_name == fp_lot.name  # noqa: B023
                        )
                        and line.component_id == move.product_id  # noqa: B023
                    )
                    if matrix_lines:
                        self._amend_reservations(move, matrix_lines)
                        self._consume_selected_lots(move, matrix_lines)

            # Complete MO and create backorder if needed.
            mos += current_mo
            # Stop copy/paste from super's button_validate
            # because then `super` marks the production as done.

            backorders = False
            if current_mo.product_qty > 1:
                backorders = current_mo._split_productions()
                current_mo.write({"product_qty": current_mo.qty_producing})
            if backorders:
                current_mo = backorders[0]
                current_mo.write({"parallel_production_id": parallel_production.id})
            else:
                break

        # Return action copy/pasted from super's button_validate
        # TODO: not specified lots: auto create lots?
        if not mos:
            mos = self.production_id
        res = {
            "domain": [("id", "in", mos.ids)],
            "name": _("Manufacturing Orders"),
            "src_model": "mrp.production.serial.matrix",
            "view_type": "form",
            "view_mode": "list,form",
            "view_id": False,
            "views": False,
            "res_model": "mrp.production",
            "type": "ir.actions.act_window",
        }
        return res
