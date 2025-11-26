from odoo import api, fields, models


class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    is_reserved_or_used = fields.Boolean(
        compute="_compute_is_reserved_or_used",
        store=True,
        help="Technical field to forbid reservation of lots already present in other "
        "MOs or reserved",
    )
    producing_production_ids = fields.One2many(
        comodel_name="mrp.production",
        inverse_name="lot_producing_id",
    )
    stock_move_line_ids = fields.One2many(
        comodel_name="stock.move.line",
        inverse_name="lot_id",
    )
    reserved_production_ids = fields.Many2many(
        comodel_name="mrp.production",
        relation="mrp_production_stock_production_lot_rel",
        column1="stock_production_lot_id",
        column2="mrp_production_id",
    )

    @api.depends(
        "producing_production_ids",
        "reserved_production_ids",
        "stock_move_line_ids",
    )
    def _compute_is_reserved_or_used(self):
        for lot in self:
            lot.is_reserved_or_used = bool(
                lot
                in (
                    lot.producing_production_ids.filtered(
                        lambda prod: prod.state != "cancel"
                    ).mapped("lot_producing_id")
                    | lot.reserved_production_ids.filtered(
                        lambda prod: prod.state != "cancel"
                    ).mapped("reserved_lot_ids")
                    | lot.stock_move_line_ids.filtered(
                        lambda ml: ml.move_id.production_id
                        and ml.move_id.production_id.state != "cancel"
                    ).mapped(
                        "lot_id"
                    )
                )
            )
