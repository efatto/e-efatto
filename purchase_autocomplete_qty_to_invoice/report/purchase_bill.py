# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, tools


class PurchaseBillUnion(models.Model):
    _inherit = "purchase.bill.union"

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """
            CREATE OR REPLACE VIEW purchase_bill_union AS (
                SELECT DISTINCT
                    po.id, po.name, po.partner_ref as reference, po.partner_id,
                    po.date_order::date as date, po.amount_untaxed as amount,
                    po.currency_id, po.company_id, NULL as vendor_bill_id,
                    po.id as purchase_order_id
                FROM purchase_order po
                LEFT JOIN purchase_order_line pol ON pol.order_id = po.id 
                WHERE
                    pol.qty_to_invoice <> 0.0
                    AND po.state in ('purchase', 'done') AND
                    po.invoice_status in ('to invoice', 'no')
            )"""
        )
