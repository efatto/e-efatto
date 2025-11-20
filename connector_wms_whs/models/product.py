from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.connector_whs.models.base_external_dbsource import clean_sql_text


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def show_whs_syncronization_records(self):
        res = super().show_whs_syncronization_records()
        contents = ""
        dbsource = self.env["base.external.dbsource"].search(
            [("company_id", "=", self.company_id.id)], limit=1
        )
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_("Failed to open connection!"))
        sql_result = dbsource.execute_mssql(
            sqlquery=clean_sql_text("SELECT * FROM HOST_ARTICOLI WHERE Codice=:Codice"),
            sqlparams={"Codice": self.default_code},
            metadata=None,
        )
        if sql_result[0]:
            contents = _(
                "Product is going to be synchronized with WHS with record: %s."
                % str(sql_result[0])
            )
        else:
            contents = _("Product is going to be synchronized with WHS.")
        res["params"].update(
            {
                "message": contents,
            }
        )
        return res
