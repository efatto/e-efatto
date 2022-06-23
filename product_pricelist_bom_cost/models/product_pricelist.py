# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"
    _order = "applied_on, min_quantity desc, min_value desc, categ_id desc, id desc"

    base = fields.Selection(
        selection_add=[('bom_cost', 'Bom Cost')]
    )
    applied_on = fields.Selection(
        selection_add=[('21_listprice_category', 'Listprice Category')]
    )
    listprice_categ_id = fields.Many2one(
        comodel_name='listprice.category',
        string='Listprice Category',
        ondelete='cascade',
        help="Specify listprice product category on which this rule is applicable"
    )
    min_value = fields.Monetary(
        help="Value above or equal this one will be included in this rule."
    )
    max_value = fields.Monetary(
        help="Value under this value will be included in this rule."
    )

    @api.multi
    @api.constrains('min_value', 'max_value')
    def check_overlap(self):
        for rec in self:
            if rec.min_value >= rec.max_value:
                raise ValidationError(
                    _('Min value must be minor and different of max value!')
                )
            value_domain = [
                ('pricelist_id', '=', rec.pricelist_id.id),
                ('listprice_categ_id', '=', rec.listprice_categ_id.id),
                ('id', '!=', rec.id),
                ('min_value', '<', rec.max_value),
                ('max_value', '>', rec.min_value)]
            overlap = self.search(value_domain)
            if overlap:
                raise ValidationError(
                    _('Overlapping value in pricelist: %s-%s overlaps with %s-%s') %
                    (rec.name, rec.price, overlap[0].name, overlap[0].price))

    @api.one
    @api.depends('categ_id', 'product_tmpl_id', 'product_id', 'compute_price',
                 'fixed_price', 'pricelist_id', 'percent_price', 'price_discount',
                 'price_surcharge')
    def _get_pricelist_item_name_price(self):
        super()._get_pricelist_item_name_price()
        if self.listprice_categ_id:
            self.name = _("Listprice Category: %s") % self.listprice_categ_id.name
