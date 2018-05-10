# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class StockPickingPackagePreparation(models.Model):
    _inherit = 'stock.picking.package.preparation'

    agent_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='ddt_agent_ids_rel',
        column1='ddt_id', column2='agent_id',
        compute='_get_ddt_agent_ids',
        string="Agents",
        help='Technical field to use when needed (like send mail).'
    )

    @api.depends('sale_ids')
    @api.multi
    def _get_ddt_agent_ids(self):
        for ddt in self:
            agent_ids = ddt.sale_ids.mapped('agent_ids')
            if agent_ids:
                ddt.agent_ids = agent_ids.ids
