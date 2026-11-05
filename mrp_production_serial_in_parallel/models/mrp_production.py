from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_round


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    parallel_production_id = fields.Many2one(
        comodel_name="mrp.production",
        copy=False,
        readonly=True,
    )
    is_parallel_production = fields.Boolean(
        string="Is Parallel Production of Serial Products?",
        compute="_compute_is_parallel_production",
        store=True,
    )

    @api.depends(
        "product_id.tracking",
        "product_qty",
        "parallel_production_id",
    )
    def _compute_is_parallel_production(self):
        for record in self:
            record.is_parallel_production = bool(
                record.product_id.tracking == "serial"
                and record.product_qty != 1
                and not record.parallel_production_id
            )

    def _compute_show_serial_matrix(self):
        res = super()._compute_show_serial_matrix()
        for rec in self:
            # show whenever qty to produce or producing is not 1
            rec.show_serial_matrix = rec.product_id.tracking == "serial" and (
                rec.product_qty > 1 or rec.qty_producing > 1
            )
        return res

    def _set_qty_producing(self, pick_manual_consumption_moves=True):
        if self.env.context.get("production_serial_matrix"):
            # recompute qty using quantity done to preserve user's changes
            if self.product_id.tracking == "serial":
                qty_producing_uom = self.product_uom_id._compute_quantity(
                    self.qty_producing,
                    self.product_id.uom_id,
                    rounding_method="HALF-UP",
                )
                if qty_producing_uom != 1:
                    self.qty_producing = self.product_id.uom_id._compute_quantity(
                        1, self.product_uom_id, rounding_method="HALF-UP"
                    )

            for move in self.move_raw_ids | self.move_finished_ids.filtered(
                lambda m: m.product_id != self.product_id
            ):
                if (
                    move._should_bypass_set_qty_producing() or not move.product_uom
                ) and not move.quantity:
                    continue
                if move.quantity and float_compare(
                    move.quantity,
                    move.product_uom_qty,
                    precision_rounding=move.product_uom.rounding,
                ):
                    # qty done is set but was not expected
                    if self.env.context.get("first_production_serial_matrix"):
                        # 1. it's linked to a bom line, then we fix the value
                        # 2. it's created from scratch, so we use the production
                        # total qty as division's factor
                        current_qty = (
                            move.quantity / self.parallel_production_id.product_qty
                        )
                    else:
                        # 3. it's already been corrected
                        current_qty = move.quantity
                else:
                    if move.bom_line_id:
                        # 1. it's linked to a bom line, then we use default compute
                        current_qty = (
                            self.qty_producing - self.qty_produced
                        ) * move.unit_factor
                    else:
                        # 2. it's created from scratch
                        if self.env.context.get("first_production_serial_matrix"):
                            # it's the first production, so we use the production total
                            # qty as division's factor
                            current_qty = (
                                move.product_uom_qty
                                / self.parallel_production_id.product_qty
                            )
                        else:
                            if move.quantity:
                                # 3. it's already been corrected
                                current_qty = move.quantity
                            else:
                                # 4. it's not been corrected, so we use default compute
                                current_qty = (
                                    self.qty_producing - self.qty_produced
                                ) * move.unit_factor
                new_qty = float_round(
                    current_qty, precision_rounding=move.product_uom.rounding
                )
                move.move_line_ids.filtered(
                    lambda ml: ml.state not in ("done", "cancel")
                ).write({"quantity": 0})
                move.move_line_ids = move._set_quantity_done_prepare_vals(new_qty)
            return True

        return super()._set_qty_producing(pick_manual_consumption_moves)

    def _split_productions(
        self, amounts=False, cancel_remaining_qty=False, set_consumed_qty=False
    ):
        res = super()._split_productions(
            amounts=amounts,
            cancel_remaining_qty=cancel_remaining_qty,
            set_consumed_qty=set_consumed_qty,
        )
        backorders = res - self
        if self.parallel_production_id:
            # Keep every serial production linked to the same parallel production,
            # even when the matrix is interrupted before processing all of them.
            backorders.write({"parallel_production_id": self.parallel_production_id.id})
        return res

    def _check_reserved_lot_qty(self):
        for record in self:
            if record.reserved_lot_ids and record.product_qty != len(
                record.reserved_lot_ids
            ):
                raise ValidationError(
                    _(
                        "The number of reserved lots must be equal to the quantity of "
                        "finished products."
                    )
                )
