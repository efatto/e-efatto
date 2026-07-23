from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.connector_whs.models.base_external_dbsource import clean_sql_text


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
SELECT ha.Codice, ha.Descrizione AS Descrizione, ha.id AS id_articoli, 0 AS id_giacenza, ha.Peso AS peso_articoli, 0 AS peso_giacenza, 0 AS qta FROM HOST_ARTICOLI ha
WHERE ha.Codice=:Codice
UNION
SELECT hg.Articolo, '' AS Descrizione, 0 AS id_articoli, hg.id AS id_giacenza, 0 AS peso_articoli, hg.Peso AS peso_giacenza, hg.Qta AS qta FROM HOST_GIACENZE hg
WHERE hg.Articolo=:Codice
                """
            ),
            sqlparams={"Codice": self.default_code},
            metadata=True,
        )
        if sql_result[0]:
            cols = sql_result[1]
            rows_with_headers = [dict(zip(cols, row)) for row in sql_result[0]]
            contents = _(
                "Product info in table HOST_ARTICOLI and HOST_GIACENZE: %s."
                % str(rows_with_headers)
            )
        else:
            contents = _("No info found for this product.")
        res["params"].update(
            {
                "message": contents,
            }
        )
        return res
