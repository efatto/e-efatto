from odoo import api, fields, models, _
from collections import defaultdict
from odoo.exceptions import UserError
from odoo.addons.stock.models.product import OPERATORS
from datetime import datetime, timedelta


class StockPicking(models.Model):
    _inherit = "stock.picking"

    forecast_expected_date = fields.Datetime(
        related="move_lines.forecast_expected_date",
    )


class StockMove(models.Model):
    _inherit = "stock.move"

    forecast_expected_date = fields.Datetime(
        search='_search_forecast_expected_date')

    @api.model
    def _search_forecast_expected_date(self, operator, value):
        if operator not in ("<", ">", "=", "!=", "<=", ">="):
            raise UserError(_("Invalid domain operator %s") % operator)
        value_dt = fields.Datetime.from_string(value)
        if not isinstance(value_dt, datetime):
            raise UserError(_("Invalid domain right operand %s") % value_dt)
        move_expected_date_dict = {}
        product_moves = self.search([
            ("state", "not in", ['cancel', 'done']),
            ("product_id.type", "=", "product"),
        ])
        warehouse_by_location = {
            loc: loc.get_warehouse() for loc in product_moves.location_id}

        outgoing_unreserved_moves_per_warehouse = defaultdict(
            lambda: self.env['stock.move'])
        for move in product_moves:
            picking_type = move.picking_type_id or move.picking_id.picking_type_id
            is_unreserved = move.state in (
                'waiting', 'confirmed', 'partially_available')
            if picking_type.code in self._consuming_picking_types() and is_unreserved:
                outgoing_unreserved_moves_per_warehouse[warehouse_by_location[
                    move.location_id]] |= move

        for warehouse, moves in outgoing_unreserved_moves_per_warehouse.items():
            if not warehouse:  # No prediction possible if no warehouse.
                continue
            product_variant_ids = moves.product_id.ids
            wh_location_ids = [
                loc['id'] for loc in self.env['stock.location'].search_read(
                    [('id', 'child_of', warehouse.view_location_id.id)],
                    ['id'],
                )
            ]
            ForecastedReport = self.env[
                'report.stock.report_product_product_replenishment']
            forecast_lines = ForecastedReport.with_context(
                warehouse=warehouse.id)._get_report_lines(
                    None, product_variant_ids, wh_location_ids)
            for move in moves:
                lines = [
                    line for line in forecast_lines if line["move_out"] == move._origin
                    and line["replenishment_filled"] is True]
                if lines:
                    move_ins_lines = list(filter(
                        lambda report_line: report_line['move_in'], lines))
                    if move_ins_lines:
                        expected_date = max(m['move_in'].date for m in move_ins_lines)
                        move_expected_date_dict.update({move.id: expected_date})
        ids = []
        for move in move_expected_date_dict:
            if operator == "=":
                value_dt_end_day = value_dt + timedelta(days=1)
                if (
                    value_dt <= move_expected_date_dict[move] <= value_dt_end_day
                ):
                    ids.append(move)
            if OPERATORS[operator](move_expected_date_dict[move], value_dt):
                ids.append(move)
        return [("id", "in", ids)]
