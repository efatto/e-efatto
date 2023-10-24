# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
# from odoo import _, models
#
#
# class StockMove(models.Model):
#     _inherit = "stock.move"
#
#     def _prepare_phantom_move_values(self, bom_line, product_qty, quantity_done):
#         res = super()._prepare_phantom_move_values(
#             bom_line, product_qty, quantity_done)
#         if (
#             self.warehouse_id._find_global_route(
#                 "stock.route_warehouse0_mto", _("Make To Order")
#             )
#             not in bom_line.product_id.route_ids
#         ):
#             res.update(
#                 {
#                     "procure_method": "make_to_stock",
#                 }
#             )
#         return res
