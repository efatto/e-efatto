from odoo import api, fields, models
from odoo.tools import config


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    is_stopped = fields.Boolean(
        compute='_compute_is_stopped',
        store=True,
        copy=False)

    @api.multi
    @api.depends('move_raw_ids.state', 'product_id.route_ids',
                 'product_id.seller_ids')
    def _compute_is_stopped(self):
        # stop procurement for all production order which product has a
        # purchase route and a subcontractor
        buy_route = self.env.ref("purchase_stock.route_warehouse0_buy")
        for production in self:
            # produce route is obviously already present
            is_stopped = bool(
                any(
                    x.is_subcontractor for x in
                    production.mapped("product_id.seller_ids")
                )
                and buy_route in production.product_id.route_ids
                and not production.purchase_order_id
            )
            production.is_stopped = is_stopped

    @api.multi
    def _generate_moves(self):
        # Overloaded to pass the context to block procurement run
        for prod in self:
            prod = prod.with_context(is_stopped=prod.is_stopped)
            super(MrpProduction, prod)._generate_moves()
            if not config['test_enable'] or self.env.context.get(
                'test_mrp_manual_procurement_subcontractor'
            ):
                # restore initial 'draft' state for all raw moves
                prod.move_raw_ids.write({'state': 'draft'})
        return True

    @api.multi
    def button_start_procurement(self):
        self.ensure_one()
        self._adjust_procure_method()
        self.move_raw_ids.filtered(lambda x: x.state == 'draft')._action_confirm()
