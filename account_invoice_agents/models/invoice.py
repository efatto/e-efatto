# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    agent_ids = fields.Many2many(
        comodel_name='res.partner',
        compute='_get_invoice_agent_ids',
        store=True,
        string="Agents",
        help='Technical field to use when needed (like send mail).'
    )

    @api.multi
    def _get_invoice_agent_ids(self):
        for inv in self:
            agent_ids = inv.invoice_line.mapped('agents.agent')
            if agent_ids:
                inv.agent_ids = agent_ids.ids
