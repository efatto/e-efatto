from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    enable_supplierinfo_management = fields.Boolean()

    # todo check children pricelist have this boolean active?


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    enable_supplierinfo_management = fields.Boolean(
        related='pricelist_id.enable_supplierinfo_management'
    )

    @api.constrains('compute_price', 'enable_supplierinfo_management')
    def check_compute_price(self):
        for item in self.filtered('pricelist_id.enable_supplierinfo_management'):
            if item.compute_price != 'formula':
                raise ValidationError(
                    _('Item of pricelist with supplierinfo managament enabled '
                      'cannot hava a compute price different of formula!')
                )
