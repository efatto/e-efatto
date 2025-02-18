
from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    purchase_price = fields.Float('Cost')
    estimated_purchase_price = fields.Float('Estimated Cost')
    final_purchase_price = fields.Float('Final Cost')

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        if fields is None:
            fields = {}
        fields['purchase_price'] = """
, SUM(l.purchase_price / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE
s.currency_rate END) AS purchase_price"""
        fields['estimated_purchase_price'] = """
, SUM(l.estimated_purchase_price / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0
ELSE s.currency_rate END) AS estimated_purchase_price"""
        fields['estimated_purchase_price'] = """
, SUM(l.final_purchase_price / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0
ELSE s.currency_rate END) AS final_purchase_price"""
        return super()._query(with_clause, fields, groupby, from_clause)
