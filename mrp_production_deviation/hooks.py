import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def set_price_unit_production_component_moves(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    stock_move_obj = env["stock.move"]
    stock_moves = stock_move_obj.search(
        [
            ("raw_material_production_id", "!=", False),
            ("state", "!=", "cancel"),
            ("date", ">", "2024-12-31"),
            "|",
            ("price_unit", "=", 0),
            ("price_unit", "=", False),
        ]
    )
    _logger.info("Updating #%s components stock_move price unit" % len(stock_moves))
    for stock_move in stock_moves:
        if stock_move.product_id.standard_price:
            stock_move.price_unit = stock_move.product_id.standard_price
