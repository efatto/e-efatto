# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    purchase_delay = fields.Float(
        'Purchase Lead Time', compute='_get_purchase_delay',
        store=True, default=0.0,
        help="Lead time in days to purchase this product. "
             "Computed from delay of first seller.")

    @api.depends('seller_ids', 'seller_ids.delay')
    def _get_purchase_delay(self):
        for product_tmpl in self.filtered(
            lambda x: x.seller_ids and x.purchase_ok
        ):
            product_tmpl.purchase_delay = product_tmpl.seller_ids[:1].delay
