# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import time
from odoo import api, fields, models, _


class ReplenishmentCost(models.Model):
    _name = 'replenishment.cost'
    _description = 'Product Replenishment Cost'

    name = fields.Char()
    last_update = fields.Datetime()
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
    )
    product_ctg_ids = fields.Many2many(
        comodel_name='product.category',
        string='Product Categories'
    )
    log = fields.Text()
    missing_seller_ids = fields.Many2many(
        comodel_name='product.product',
        relation='repl_missing_seller_rel',
        column1='repl_id',
        column2='prod_id',
        string="Product missing seller")
    missing_seller_price_ids = fields.Many2many(
        comodel_name='product.product',
        relation='repl_missing_price_rel',
        column1='repl_id',
        column2='prod_id',
        string="Product missing price")

    @api.multi
    def update_products_standard_price_and_replenishment_cost(self):
        res = self.with_context(
            update_standard_price=True,
            update_managed_replenishment_cost=True,
        ).update_products_replenishment_cost()
        return res

    @api.multi
    def update_products_standard_price_only(self):
        res = self.with_context(
            update_standard_price=True,
        ).update_products_replenishment_cost()
        return res

    @api.multi
    def update_products_replenishment_cost_only(self):
        res = self.with_context(
            update_managed_replenishment_cost=True,
        ).update_products_replenishment_cost()
        return res

    @api.multi
    def update_products_replenishment_cost(self):
        for repl in self:
            domain = [('type', 'in', ['product', 'consu', 'service'])]
            if repl.product_ctg_ids:
                domain.append(('categ_id', 'in', repl.product_ctg_ids.ids))
            products = self.env['product.product'].search(domain)
            started_at = time.time()
            products_without_seller, products_without_seller_price = \
                products.update_managed_replenishment_cost()
            duration = time.time() - started_at
            last_update = fields.Datetime.now()
            if not repl.name:
                repl.name = _('Update of %s' % last_update)
            repl.write(dict(
                last_update=last_update,
                log='Updated %s %s for %s products in %.2f minutes.' % (
                    '"standard price"'
                    if self.env.context.get('update_standard_price')
                    else '',
                    '"replenishment cost"'
                    if self.env.context.get('update_managed_replenishment_cost')
                    else '',
                    len(products),
                    duration / 60,
                    ),
                )
            )
            repl.missing_seller_ids = products_without_seller
            repl.missing_seller_price_ids = products_without_seller_price
        return True
