# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    sale_order_ids = fields.One2many(
        'sale.order',
        'purchase_order_id',
        string='Linked Sale Offer'
    )

    #todo bottone per scollegare le offerte collegate