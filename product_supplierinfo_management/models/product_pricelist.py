from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    enable_supplierinfo_management = fields.Boolean()

    # todo check children pricelist have this boolean active?


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    @api.constrains('compute_price')
    def check_compute_price(self):
        for item in self.filtered('pricelist_id.enable_supplierinfo_management'):
            if item.compute_price != 'formula':
                raise ValidationError(
                    _('Item of pricelist with supplierinfo managament enabled '
                      'cannot have a compute price different of formula!')
                )
