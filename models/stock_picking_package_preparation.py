# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class StockPickingPackagePreparation(models.Model):
    _inherit = 'stock.picking.package.preparation'

    @api.multi
    def _get_related_sales(self):
        for sppp in self:
            if sppp.picking_ids:
                sppp.sale_ids = sppp.picking_ids.mapped('sale_id')

    sale_ids = fields.Many2many(
        comodel_name='sale.order',
        compute=_get_related_sales,
    )
