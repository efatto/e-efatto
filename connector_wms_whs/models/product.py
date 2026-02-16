from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.connector_whs.models.base_external_dbsource import clean_sql_text


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def show_whs_syncronization_records(self):
        return self.product_variant_ids.show_whs_syncronization_records()


class ProductProduct(models.Model):
    _inherit = "product.product"

    def show_whs_syncronization_records(self):
        res = super().show_whs_syncronization_records()
        dbsource = self.env["base.external.dbsource"].search(
            [("company_id", "=", self.company_id.id)], limit=1
        )
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_("Failed to open connection!"))
        sql_result = dbsource.execute_mssql(
            sqlquery=clean_sql_text(
                """
SELECT * FROM HOST_ARTICOLI ha
INNER JOIN (
    SELECT hg.Articolo
    FROM (
        SELECT *, ROW_NUMBER() OVER(PARTITION BY Articolo ORDER BY id DESC) Corr
        FROM HOST_GIACENZE
    ) hg
    WHERE hg.Corr = 1
) hglast
ON ha.Codice = hglast.Articolo
INNER JOIN (
    SELECT hap.id
    FROM (
        SELECT *, ROW_NUMBER() OVER(PARTITION BY Codice ORDER BY id DESC) Corr1
        FROM HOST_ARTICOLI
    ) hap
    WHERE hap.Corr1 = 1
) hglasta
ON ha.id = hglasta.id
WHERE ha.Codice=:Codice
                """
            ),
            sqlparams={"Codice": self.default_code},
            metadata=True,
        )
        if sql_result[0]:
            cols = sql_result[1]
            rows_with_headers = [dict(zip(cols, row)) for row in sql_result[0]]
            contents = _(
                "Product is going to be synchronized with WHS with record: %s."
                % str(rows_with_headers)
            )
        else:
            contents = _("Product is going to be synchronized with WHS.")
        res["params"].update(
            {
                "message": contents,
            }
        )
        return res
