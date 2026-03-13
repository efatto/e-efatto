from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.connector_whs.models.base_external_dbsource import clean_sql_text


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

    def action_name_is_too_long(self):
        raise UserError(_("Product name is too long!"))

    def action_wms_modula_error(self):
        raise UserError(
            _("Error importing product on WMS Modula: %s" % self.wms_modula_error)
        )

    def show_whs_syncronization_records(self):
        res = super().show_whs_syncronization_records()
        dbsource = self.env["base.external.dbsource"].search(
            [("company_id", "=", (self.company_id or self.env.user.company_id).id)],
            limit=1,
        )
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_("Failed to open connection!"))
        sql_result = dbsource.execute_mssql(
            sqlquery=clean_sql_text(
                """
SELECT * FROM EXP_GIACENZE ha
INNER JOIN (
    SELECT hg.UBI_ARTICOLO
    FROM (
        SELECT *, ROW_NUMBER() OVER(PARTITION BY UBI_ARTICOLO ORDER BY UBI_DATAORAS1 DESC) Corr
        FROM EXP_UBICAZIONI
    ) hg
    WHERE hg.Corr = 1
) hglast
ON ha.GIA_ARTICOLO = hglast.UBI_ARTICOLO
INNER JOIN (
    SELECT hap.UBI_ARTICOLO
    FROM (
        SELECT *, ROW_NUMBER() OVER(PARTITION BY UBI_ARTICOLO ORDER BY UBI_DATAORAS1 DESC) Corr1
        FROM EXP_UBICAZIONI
    ) hap
    WHERE hap.Corr1 = 1
) hglasta
ON ha.GIA_ARTICOLO = hglasta.UBI_ARTICOLO
WHERE ha.GIA_ARTICOLO=:Codice
                """
            ),
            sqlparams={"Codice": self.default_code},
            metadata=True,
        )
        if sql_result[0]:
            cols = sql_result[1]
            rows_with_headers = [dict(zip(cols, row)) for row in sql_result[0]]
            contents = _("Product stock in WMS info: %s." % str(rows_with_headers))
        else:
            contents = _("Product stock in WMS info not found.")
        res["params"].update(
            {
                "message": contents,
            }
        )
        return res
