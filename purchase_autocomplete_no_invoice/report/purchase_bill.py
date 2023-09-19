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
                SELECT
                    id, name, partner_ref as reference, partner_id,
                    date_order::date as date, amount_untaxed as amount, currency_id,
                    company_id, NULL as vendor_bill_id, id as purchase_order_id
                FROM purchase_order
                WHERE
                    state in ('purchase', 'done') AND
                    invoice_status in ('to invoice', 'no')
            )"""
        )
