# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class StockPickingPackagePreparation(models.Model):
    _inherit = 'stock.picking.package.preparation'

    tobeinvoiced = fields.Boolean(
        compute='_tobeinvoiced',
        search='_search_tobeinvoiced',
    )

    @api.depends('picking_ids')
    def _tobeinvoiced(self):
        for pack in self:
            if any(picking.invoice_state == '2binvoiced' for picking in
                    pack.picking_ids):
                pack.tobeinvoiced = True
            else:
                pack.tobeinvoiced = False

    @staticmethod
    def _search_tobeinvoiced(self, operator, value):
        if operator == '=' and value is True:
            return [('picking_ids.invoice_state', '=', '2binvoiced')]
        if operator == '!=' and value is True:
            return ['|',
                    ('picking_ids.invoice_state', '!=', '2binvoiced'),
                    ('picking_ids', '=', False)
                    ]
