from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    name_wms_modula = fields.Char(
        string="WMS Modula Name",
        compute="_compute_name_wms_modula",
        store=True,
        index=True,
    )
    is_name_too_long = fields.Boolean(
        string="Name is too long",
        compute="_compute_name_wms_modula",
        store=True,
        index=True,
    )

    @api.depends("name")
    def _compute_name_wms_modula(self):
        for product_tmpl in self:
            is_name_too_long = False
            if product_tmpl.name:
                if len(product_tmpl.name) > 100:
                    name_wms_modula = product_tmpl.name[:94] + " [...]"
                    is_name_too_long = True
                else:
                    name_wms_modula = product_tmpl.name
            else:
                name_wms_modula = _(
                    "Missing product template ID: %s name"
                ) % product_tmpl.id
            product_tmpl.name_wms_modula = name_wms_modula
            product_tmpl.is_name_too_long = is_name_too_long
