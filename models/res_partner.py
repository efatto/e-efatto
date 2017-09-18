# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    CAF_number = fields.Integer(
       size=5, help="Optional C.A.F. number")
    codice_carica = fields.Many2one(
        comodel_name='codice.carica')


class AccountPeriod(models.Model):
    _inherit = "account.period"

    invoice_statement_id = fields.Many2one(
        comodel_name='invoice.statement')
