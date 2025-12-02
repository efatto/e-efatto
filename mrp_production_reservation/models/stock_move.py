from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    is_fully_reserved = fields.Boolean(
        compute="_compute_is_fully_reserved",
        store=True,
        string=" ",
        help="This move is fully reserved.",
    )

    @api.depends("reserved_availability", "product_uom_qty")
    def _compute_is_fully_reserved(self):
        for move in self:
            move.is_fully_reserved = bool(
                move.reserved_availability == move.product_uom_qty
                or move.product_id.type != "product"
            )

    #
    #
    # def _get_relevant_state_among_moves(self):
    #     """
    #     Changed logic to consider reserved state too.
    #     :return:
    #     """
    #     # We sort our moves by importance of state:
    #     #     ------------- 0
    #     #     | Assigned  |
    #     #     -------------
    #     #     |  Waiting  |
    #     #     -------------
    #     #     |  Partial  |
    #     #     -------------
    #     #     |  Confirm  |
    #     #     ------------- len-1
    #     super()._get_relevant_state_among_moves()
    #     sort_map = {
    #         'assigned': 4,
    #         'waiting': 3,
    #         'partially_available': 2,
    #         'confirmed': 1,
    #     }
    #     moves_todo = self\
    #         .filtered(lambda move: move.state not in ['cancel', 'done']
    #         and not (move.state == 'assigned' and not move.product_uom_qty))\
    #         .sorted(key=lambda move: (sort_map.get(move.state, 0),
    #         move.product_uom_qty))
    #     if not moves_todo:
    #         return 'assigned'
    #     # The picking should be the same for all moves.
    #     if moves_todo[:1].picking_id and moves_todo[:1].picking_id.move_type == 'one':
    #         most_important_move = moves_todo[0]
    #         if most_important_move.state == 'confirmed':
    #             return 'confirmed' if most_important_move.product_uom_qty else
    #             'assigned'
    #         elif most_important_move.state == 'partially_available':
    #             return 'confirmed'
    #         else:
    #             if moves_todo[:1].state == 'assigned'
    #             and moves_todo[:1].is_fully_reserved:
    #                 return moves_todo[:1].state
    #             else:
    #                 return moves_todo[:1].state or 'draft'
    #     elif moves_todo[:1].state != 'assigned' and any(move.state in [
    #           'assigned', 'partially_available'] for move in moves_todo):
    #         return 'partially_available'
    #     else:
    #         least_important_move = moves_todo[-1:]
    #         if least_important_move.state == 'confirmed'
    #         and least_important_move.product_uom_qty == 0:
    #             return 'assigned'
    #         # todo quindi considera assegnati se senza quantità?
    #         else:
    #             return moves_todo[-1:].state or 'draft'
