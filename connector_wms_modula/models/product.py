from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    name_wms_modula = fields.Char(
        string="WMS Modula Name",
        compute="_compute_name_wms_modula",
        inverse="_inverse_name_wms_modula",
        store=True,
        index=True,
    )
    custom_name_wms_modula = fields.Char(
        string="Technical field to store WMS Modula name",
    )
    is_name_too_long = fields.Boolean(
        string="Name is too long",
        compute="_compute_name_wms_modula",
        store=True,
        index=True,
    )
    wms_modula_error = fields.Char(
        string="Error importing the product on WMS Modula",
    )

    @api.constrains("custom_name_wms_modula")
    def _constrains_custom_name_wms_modula(self):
        for rec in self:
            if rec.custom_name_wms_modula:
                if len(rec.custom_name_wms_modula) > 100:
                    raise UserError(
                        _("Product name for WMS Modula max lenght is 100 char!")
                    )

    @api.constrains("default_code")
    def _constrains_default_code(self):
        for rec in self:
            if rec.default_code:
                if len(rec.default_code) > 50:
                    raise UserError(_("Product default code max length is 50 char!"))

    def _inverse_name_wms_modula(self):
        for rec in self:
            if rec.name_wms_modula:
                rec.custom_name_wms_modula = rec.name_wms_modula

    @api.depends("name", "custom_name_wms_modula")
    def _compute_name_wms_modula(self):
        for product_tmpl in self:
            is_name_too_long = False
            if product_tmpl.custom_name_wms_modula:
                name_wms_modula = product_tmpl.custom_name_wms_modula
            elif product_tmpl.name:
                if len(product_tmpl.name) > 100:
                    name_wms_modula = product_tmpl.name[:94] + " [...]"
                    is_name_too_long = True
                else:
                    name_wms_modula = product_tmpl.name
            else:
                name_wms_modula = (
                    _("Missing product template ID: %s name") % product_tmpl.id
                )
            product_tmpl.name_wms_modula = name_wms_modula
            product_tmpl.is_name_too_long = is_name_too_long

    def action_name_is_too_long(self):
        raise UserError(_("Product name is too long!"))

    def action_wms_modula_error(self):
        raise UserError(
            _("Error importing product on WMS Modula: %s" % self.wms_modula_error)
        )


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _get_product_to_sync(self, last_date):
        return self.search(
            [
                "|",
                ("write_date", ">", last_date),
                ("product_tmpl_id.write_date", ">", last_date),
                ("type", "=", "product"),
                ("default_code", "!=", False),
                ("default_code", "!=", " "),
            ]
        )
