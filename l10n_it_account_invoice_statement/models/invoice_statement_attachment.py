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
    dtr_statement_id = fields.One2many(
        comodel_name='invoice.statement',
        inverse_name='dtr_attachment_id',
        string="Invoice Statement",
        readonly=True)
    dte_statement_id = fields.One2many(
        comodel_name='invoice.statement',
        inverse_name='dte_attachment_id',
        string="Invoice Statement",
        readonly=True)
    ann_dtr_statement_id = fields.One2many(
        comodel_name='invoice.statement',
        inverse_name='ann_dtr_attachment_id',
        string="Invoice Statement",
        readonly=True)
    ann_dte_statement_id = fields.One2many(
        comodel_name='invoice.statement',
        inverse_name='ann_dte_attachment_id',
        string="Invoice Statement",
        readonly=True)
    # name = fields.Char()
    # type = fields.Selection(
    #     related='statement_id.type'
    # )
