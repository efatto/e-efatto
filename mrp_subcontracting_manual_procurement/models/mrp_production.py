from odoo import api, fields, models
from odoo.tools import config


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    is_procurement_stopped = fields.Boolean(
        compute='_compute_is_procurement_stopped', store=True, copy=False)

    @api.multi
    @api.depends('move_raw_ids.state', 'move_raw_ids.product_id.seller_ids')
    def _compute_is_procurement_stopped(self):
        for production in self:
            if production.move_raw_ids:
                is_procurement_stopped = bool(
                    any(
                        x.is_subcontractor for x in
                        production.mapped("move_raw_ids.product_id.seller_ids")
                    )
                    and
                    any(
                        y.state == 'draft' for y in production.move_raw_ids
                    )
                )
            else:
                is_procurement_stopped = False
            production.is_procurement_stopped = is_procurement_stopped

    @api.multi
    def _generate_moves(self):
        # Overloaded to pass the context to block procurement run
        for prod in self:
            prod = prod.with_context(is_procurement_stopped=prod.is_procurement_stopped)
            super(MrpProduction, prod)._generate_moves()
            if not config['test_enable'] \
                    or self.env.context.get('test_mrp_subcontracting_manual_procurement'):
                # restore initial 'draft' state
                move_subcontractor = self.env['stock.move']
                for move in prod.move_raw_ids:
                    if any(x.is_subcontractor for x in move.product_id.seller_ids):
                        move_subcontractor |= move
                move_subcontractor.write({'state': 'draft'})
        return True

    @api.multi
    def button_start_procurement(self):
        self.ensure_one()
        self._adjust_procure_method()
        self.move_raw_ids.filtered(lambda x: x.state == 'draft')._action_confirm()
