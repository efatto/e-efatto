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

    def _set_qty_producing(self):
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
                ) and not move.quantity_done:
                    continue
                if move.quantity_done and float_compare(
                    move.quantity_done,
                    move.product_uom_qty,
                    precision_rounding=move.product_uom.rounding,
                ):
                    if self.env.context.get("first_production_serial_matrix"):
                        if move.bom_line_id:
                            # 1. it's linked to a bom line, then we fix the value
                            current_qty = (
                                move.quantity_done
                                / self.parallel_production_id.product_qty
                            )
                        else:
                            # 2. it's created from scratch, so we use the production
                            # total qty as division's factor
                            current_qty = (
                                move.quantity_done
                                / self.parallel_production_id.product_qty
                            )
                    else:
                        # 3. it's already been corrected
                        current_qty = move.quantity_done
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
                            # 3. it's already been corrected
                            current_qty = move.quantity_done
                new_qty = float_round(
                    current_qty, precision_rounding=move.product_uom.rounding
                )
                move.move_line_ids.filtered(
                    lambda ml: ml.state not in ("done", "cancel")
                ).qty_done = 0
                move.move_line_ids = move._set_quantity_done_prepare_vals(new_qty)
            return True

        return super()._set_qty_producing()

    def _generate_backorder_productions(self, close_mo=True):
        backorders = super()._generate_backorder_productions(close_mo=close_mo)
        if self.env.context.get("backorder_serial_matrix"):
            # align moves of backorder if it's a serial matrix:
            # - create lines if added by hand
            for move in self.move_raw_ids:
                boml_bo_move = backorders.move_raw_ids.filtered(
                    lambda m, raw_move=move: m.bom_line_id
                    and m.bom_line_id == raw_move.bom_line_id
                )
                if boml_bo_move:
                    if (
                        move.quantity_done
                        and move.product_uom_qty != move.quantity_done
                        and boml_bo_move.quantity_done != move.quantity_done
                    ):
                        if not boml_bo_move.move_line_ids:
                            boml_bo_move.write(
                                {
                                    "move_line_ids": [
                                        (
                                            0,
                                            0,
                                            {
                                                "product_uom_id": move.product_uom.id,
                                                "product_id": move.product_id.id,
                                                "location_id": move.location_id.id,
                                                "location_dest_id": (
                                                    move.location_dest_id.id
                                                ),
                                            },
                                        )
                                    ]
                                }
                            )
                        boml_bo_move.move_line_ids = (
                            boml_bo_move._set_quantity_done_prepare_vals(
                                move.quantity_done
                            )
                        )
                elif move.quantity_done:
                    # create a new line as it was created by hand and not linked to a
                    # bom line
                    backorders.write(
                        {
                            "move_raw_ids": [
                                (
                                    0,
                                    0,
                                    {
                                        "name": move.name,
                                        "company_id": move.company_id.id,
                                        "product_id": move.product_id.id,
                                        "product_uom": move.product_uom.id,
                                        "product_uom_qty": move.product_uom_qty,
                                        "quantity_done": move.quantity_done,
                                        "raw_material_production_id": backorders.id,
                                        "reference": backorders.name,
                                        "picking_type_id": move.picking_type_id.id,
                                        "location_id": move.location_id.id,
                                        "location_dest_id": move.location_dest_id.id,
                                    },
                                )
                            ]
                        }
                    )
        return backorders

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

    def _compute_show_serial_matrix(self):
        for rec in self:
            # show whenever qty to produce or producing is not 1
            rec.show_serial_matrix = rec.product_id.tracking == "serial" and (
                rec.product_qty > 1 or rec.qty_producing > 1
            )
