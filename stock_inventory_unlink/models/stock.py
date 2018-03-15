# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, exceptions, api, _


class StockInventory(models.Model):
    _inherit = "stock.inventory"
    _order = 'date DESC'

    @api.multi
    def unlink(self):
        for inv in self:
            if inv.state == 'done':
                raise exceptions.ValidationError(_(
                    "You cannot delete a stock inventory in 'done' state."))
        return super(StockInventory, self).unlink()
