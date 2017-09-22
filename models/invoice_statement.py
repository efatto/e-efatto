# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, _, api


class InvoiceStatement(models.Model):
    _name = "invoice.statement"
    _description = "Invoice Statement"

    def _get_name(self):
        self.name = self.type + str(self.progressive_number)

    name = fields.Char(compute=_get_name)
    progressive_number = fields.Integer(readonly=True)
    statement_partner_id = fields.Many2one(
        comodel_name='res.partner', required=True,
        string='Soggetto obbligato all\'invio',
        help="Legal phisical Person or Partner which is obliged "
             "to present the invoice statement.")
    sender_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Soggetto incaricato alla trasmissione',
        help="Partner who send the statement")
    sender_date_commitment = fields.Date(required=True)
    dtr_attachment_id = fields.Many2one(
        'invoice.statement.attachment',
        'DTR Export File',
        readonly=True
    )
    dte_attachment_id = fields.Many2one(
        'invoice.statement.attachment',
        'DTE Export File',
        readonly=True
    )
    ann_dtr_attachment_id = fields.Many2one(
        'invoice.statement.attachment',
        'ANN DTR Export File',
        readonly=True
    )
    ann_dte_attachment_id = fields.Many2one(
        'invoice.statement.attachment',
        'ANN DTE Export File',
        readonly=True
    )
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
    ], string='Tipo file da esportare')

    @api.one
    def copy(self, defaults=None):
        if not defaults:
            defaults = {}
        defaults['attachment_id'] = False
        return super(InvoiceStatement, self).copy(defaults)
