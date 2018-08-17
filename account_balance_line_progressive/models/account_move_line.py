# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    _order = 'date desc, id desc'

    @api.depends('debit', 'credit')
    def _store_balance_progressive(self):
        tables, where_clause, where_params = self.with_context(
            initial_bal=True)._query_get()
        where_params = [tuple(self.ids)] + where_params
        if where_clause:
            where_clause = 'AND ' + where_clause
            where_clause = where_clause.replace('account_move_line', 'l1')
        self._cr.execute(
            """SELECT l1.id, COALESCE(SUM(l2.debit-l2.credit), 0)
            FROM account_move_line l1 
            JOIN account_move m on (m.id = l1.move_id AND m.state <> 'draft')
            LEFT JOIN account_move_line l2
            ON (l1.account_id = l2.account_id AND l1.partner_id = l2.partner_id)
            AND (l2.date < l1.date OR (l2.date = l1.date AND l2.id <= l1.id))
            WHERE l1.id IN %s """ + where_clause + " GROUP BY l1.id",
            where_params)
        for id, val in self._cr.fetchall():
            self.browse(id).balance = val

    balance = fields.Monetary(
        compute='_store_balance_progressive', store=False,
        currency_field='company_currency_id',
        help="Technical field holding the progressive debit - credit in order "
             "to open meaningful graph views from reports")
