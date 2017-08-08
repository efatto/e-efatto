# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import tools
from openerp.osv import fields, orm


class asset_asset_report(orm.Model):
    _inherit = "asset.asset.report"

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'asset_asset_report')
        cr.execute("""
            create or replace view asset_asset_report as (
                select
                    min(dl.id) as id,
                    dl.name as name,
                    dl.line_date as depreciation_date,
                    a.date_start as date_start,
                    a.date_remove as date_remove,
                    a.asset_value as asset_value,
                    dl.amount as depreciation_value,
                    (CASE WHEN dl.move_check
                      THEN dl.amount
                      ELSE 0
                      END) as posted_value,
                    (CASE WHEN NOT dl.move_check
                      THEN dl.amount
                      ELSE 0
                      END) as unposted_value,
                    dl.asset_id as asset_id,
                    dl.move_check as move_check,
                    a.category_id as asset_category_id,
                    a.partner_id as partner_id,
                    a.state as state,
                    count(dl.*) as nbr,
                    a.company_id as company_id
                from account_asset_depreciation_line dl
                    left join account_asset_asset a on (dl.asset_id=a.id)
                group by
                    dl.amount, dl.asset_id, dl.line_date, dl.name,
                    a.date_start, a.date_remove, dl.move_check, a.state,
                    a.category_id, a.partner_id, a.company_id, a.asset_value,
                    a.purchase_value, a.id, a.salvage_value
        )""")
