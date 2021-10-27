# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # force whs_list_ids creation for out confirmed
    stock_pickings = env['stock.picking'].search([
        ('state', 'in', ['waiting', 'confirmed', 'assigned']),
    ])
    for pick in stock_pickings:
        moves = pick.mapped('move_lines').filtered(
            lambda move: not move.whs_list_ids)
        moves.create_whs_list()
        for picking in moves.mapped('picking_id'):
            picking.state = 'waiting'
