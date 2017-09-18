# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, _, api


class InvoiceStatementAttachment(models.Model):
    _name = "invoice.statement.attachment"
    _description = "Invoice Statement Export File"
    _inherits = {'ir.attachment': 'ir_attachment_id'}
    _inherit = ['mail.thread']

    ir_attachment_id = fields.Many2one(
        'ir.attachment', 'Attachment', required=True, ondelete="cascade")
    invoice_statement_id = fields.One2many(
        comodel_name='invoice.statement',
        inverse_name='attachment_id',
        string="Invoice Statement",
        readonly=True)
