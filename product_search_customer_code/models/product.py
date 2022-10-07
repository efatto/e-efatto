# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models
from odoo.osv import expression


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False,
                access_rights_uid=None):
        # extends search with OR original search OR customer info code OR name
        args = (args or [])
        if len(args) == 1:
            if args[0][1] in ['ilike', 'like']:
                operator = args[0][1]
                name = args[0][2]
                customerinfo_ids = self.env['product.customerinfo'].search([
                    '|',
                    ('product_code', operator, name),
                    ('product_name', operator, name),
                ], limit=limit)
                product_tmpl_ids = customerinfo_ids.mapped('product_tmpl_id')
                if product_tmpl_ids:
                    args = expression.OR([
                        args,
                        [('product_tmpl_id', 'in', product_tmpl_ids.ids)],
                        [('id', 'in', product_tmpl_ids.mapped(
                            'product_variant_ids').ids)]
                    ])
        return super()._search(
            args, offset=offset, limit=limit, order=order, count=count,
            access_rights_uid=access_rights_uid)
