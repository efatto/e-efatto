# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.osv import osv, fields


class account_move_line(osv.osv):
    _inherit = "account.move.line"

    def _balance(self, cr, uid, ids, name, arg, context=None):
        super(account_move_line, self)._balance(
            cr, uid, ids, name, arg, context=context)
        if context is None:
            context = {}
        c = context.copy()
        c['initital_bal'] = True
        sql = """SELECT l1.id, COALESCE(SUM(l2.debit-l2.credit), 0)
                    FROM account_move_line l1 LEFT JOIN account_move_line l2
                    ON (l1.account_id = l2.account_id
                      AND (l2.date < l1.date
                      OR (l2.date = l1.date AND l2.id <= l1.id))
                      AND """ + \
                self._query_get(cr, uid, obj='l2', context=c) + \
                ") WHERE l1.id IN %s GROUP BY l1.id"

        cr.execute(sql, [tuple(ids)])
        return dict(cr.fetchall())

    def _balance_search(self, cursor, user, obj, name, args, domain=None,
                        context=None):
        return super(account_move_line, self)._balance_search(
            cursor, user, obj, name, args, domain=domain, context=context)

    _columns = {
        'balance': fields.function(_balance, fnct_search=_balance_search,
                                   string='Balance'),
    }