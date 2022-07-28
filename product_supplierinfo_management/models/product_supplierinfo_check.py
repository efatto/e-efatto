# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import time
from odoo import api, fields, models, _


class ProductSupplierinfoCheck(models.Model):
    _name = 'product.supplierinfo.check'
    _description = 'Product Supplierinfo Check'

    name = fields.Char()
    date_obsolete_supplierinfo_price = fields.Date()
    date_validity_supplierinfo = fields.Date(
        help="Date to filter date validity of supplierinfo prices"
    )
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
        relation='supplierinfo_missing_seller_rel',
        column1='supplierinfo_id',
        column2='prod_id',
        string="Product missing seller")
    missing_seller_price_ids = fields.Many2many(
        comodel_name='product.product',
        relation='supplierinfo_missing_price_rel',
        column1='supplierinfo_id',
        column2='prod_id',
        string="Product missing price")
    obsolete_seller_price_ids = fields.Many2many(
        comodel_name='product.product',
        relation='supplierinfo_obsolete_price_rel',
        column1='supplierinfo_id',
        column2='prod_id',
        string="Product obsolete price")
    listprice_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist for recomputation'
    )

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
    def check_products_supplierinfo(self):
        res = self.update_products_replenishment_cost()
        return res

    @api.multi
    def update_products_replenishment_cost(self):
        for supplierinfo_check in self:
            domain = [('purchase_ok', '=', True)]
            if supplierinfo_check.product_ctg_ids:
                domain.append(
                    ('categ_id', 'child_of', supplierinfo_check.product_ctg_ids.ids))
            products = self.env['product.product'].search(domain)
            started_at = time.time()
            products_without_seller, products_without_seller_price,\
                products_with_obsolete_price = \
                products.do_update_managed_replenishment_cost(
                    date_obsolete_supplierinfo_price=
                    supplierinfo_check.date_obsolete_supplierinfo_price,
                    date_validity_supplierinfo=
                    supplierinfo_check.date_validity_supplierinfo,
                    listprice_id=supplierinfo_check.listprice_id
                )
            duration = time.time() - started_at
            last_update = fields.Datetime.now()
            if not supplierinfo_check.name:
                supplierinfo_check.name = _('Update of %s' % last_update)
            supplierinfo_check.write(dict(
                last_update=last_update,
                log='%s for %s products in %.2f minutes.' % (
                    '"Updated standard price"'
                    if self.env.context.get('update_standard_price')
                    else
                    '"Updated replenishment cost"'
                    if self.env.context.get('update_managed_replenishment_cost')
                    else '"Checked"',
                    len(products),
                    duration / 60,
                    ),
                )
            )
            supplierinfo_check.missing_seller_ids = products_without_seller
            supplierinfo_check.missing_seller_price_ids = products_without_seller_price
            supplierinfo_check.obsolete_seller_price_ids = products_with_obsolete_price
        return True
