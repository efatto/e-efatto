# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields, _, exceptions


class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"

    def _get_production_date_planned(self):
        date_planned = fields.Datetime.now()
        production_id = self.env['mrp.production'].browse(
            self._context.get('active_id', False))
        if production_id:
            date_planned = production_id.date_planned
        return date_planned

    date_produce = fields.Datetime(
        default=_get_production_date_planned,
        string='Production date',
    )

    @api.multi
    def do_produce(self):
        date_produce = fields.Datetime.now()
        for data in self:
            date_produce = data.date_produce
        ctx = self._context.copy()
        ctx.update({'date_produce': date_produce})
        res = super(MrpProductProduce, self.with_context(ctx)).do_produce()
        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def action_done(self):
        res = super(StockMove, self).action_done()
        if self._context.get('date_produce', False):
            date_produce = self._context['date_produce']
            if date_produce > fields.Datetime.now():
                raise exceptions.ValidationError(
                    _("You can not process an actual "
                      "movement date in the future."))
            for move in self:
                move.date = date_produce
                if move.quant_ids:
                    move.quant_ids.sudo().write({'in_date': move.date})
                if move.picking_id:
                    move.picking_id.date = move.date
        return res
