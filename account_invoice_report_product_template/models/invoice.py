# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import tools
from openerp.osv import fields,osv


class AccountInvoiceReport(osv.osv):
    _inherit = "account.invoice.report"

    _columns = {
        'product_tmpl_id': fields.many2one(
            'product.template', 'Product Template',
            readonly=True)
    }

    def _select(self):
        return super(AccountInvoiceReport, self)._select()\
               + ", sub.product_tmpl_id"

    def _sub_select(self):
        return super(AccountInvoiceReport, self)._sub_select() \
               + ", pr.product_tmpl_id"

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() \
               + ", pr.product_tmpl_id"
