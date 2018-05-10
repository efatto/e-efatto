# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    agent_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='sale_order_agent_ids_rel',
        column1='order_id', column2='agent_id',
        compute='_get_sale_order_agent_ids',
        store=True,
        string="Agents",
        help='Technical field to use when needed (like send mail).'
    )

    @api.depends('order_line.agents')
    @api.multi
    def _get_sale_order_agent_ids(self):
        for order in self:
            agent_ids = order.order_line.mapped('agents.agent')
            if agent_ids:
                order.agent_ids = agent_ids.ids
