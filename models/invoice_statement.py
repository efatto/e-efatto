# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, _, api


class InvoiceStatement(models.Model):
    _name = "invoice.statement"
    _description = "Invoice Statement"

    name = fields.Char()
    progressive_number = fields.Integer(readonly=True)
    statement_partner_id = fields.Many2one(
        comodel_name='res.partner', required=True,
        help="Legal phisical Person or Partner which is obliged "
             "to present the invoice statement.")
    sender_partner_id = fields.Many2one(
        comodel_name='res.partner',
        help="Partner who send the statement")
    sender_date_commitment = fields.Date(required=True)
    attachment_id = fields.Many2one(
        comodel_name='invoice.statement.attachment',
        string='Invoice Statement Export File',
        readonly=True)
    period_ids = fields.One2many(
        comodel_name='account.period',
        inverse_name='invoice_statement_id',
        help="Periods wich will be included in statement.")
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env['res.company']._company_default_get(
            'invoice.statement'))
    type = fields.Selection([
        ('DTE', 'Fatture Emesse'),
        ('DTR', 'Fatture Ricevute'),
        ('ANN', 'Annullamento')
    ], string='Tipo fatture')

    @api.one
    def copy(self, defaults=None):
        if not defaults:
            defaults = {}
        defaults['attachment_id'] = False
        return super(InvoiceStatement, self).copy(defaults)
