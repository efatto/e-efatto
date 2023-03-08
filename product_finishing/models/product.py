from odoo import fields, models
import odoo.addons.decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_finishing = fields.Boolean()
    finishing_surcharge_percent = fields.Float(
        digits=dp.get_precision('Stock Weight')
    )
