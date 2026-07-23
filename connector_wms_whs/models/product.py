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
        sql_result_host_articoli = dbsource.execute_mssql(
            sqlquery=clean_sql_text(
                """
                    SELECT Descrizione, id, Peso FROM HOST_ARTICOLI
                    WHERE Codice=:Codice
                """
            ),
            sqlparams={"Codice": self.default_code},
            metadata=True,
        )
        sql_result_host_giacenze = dbsource.execute_mssql(
            sqlquery=clean_sql_text(
                """
                    SELECT id, Peso, Qta FROM HOST_GIACENZE
                    WHERE Articolo=:Codice
                """
            ),
            sqlparams={"Codice": self.default_code},
            metadata=True,
        )
        product_info = {
            "description": "",
            "weight_host_articoli": "",
            "weight_host_giacenze": "",
            "quantity": 0,
        }
        if sql_result_host_articoli[0]:
            cols = sql_result_host_articoli[1]
            rows_with_headers = [
                dict(zip(cols, row)) for row in sql_result_host_articoli[0]
            ]
            product_info["description"] = rows_with_headers[1]["Descrizione"]
            product_info["weight_host_articoli"] = str(
                {
                    float((rows_with_headers[i])["Peso"])
                    for i, x in enumerate(rows_with_headers)
                    if i > 0
                }
            )
        if sql_result_host_giacenze[0]:
            cols = sql_result_host_giacenze[1]
            rows_with_headers = [
                dict(zip(cols, row)) for row in sql_result_host_giacenze[0]
            ]
            product_info["weight_host_giacenze"] = str(
                {
                    float((rows_with_headers[i])["Peso"])
                    for i, x in enumerate(rows_with_headers)
                    if i > 0
                }
            )
            product_info["quantity"] = sum(
                float(x["Qta"]) for i, x in enumerate(rows_with_headers) if i > 0
            )
        contents = _(
            "Product info in table HOST_ARTICOLI and HOST_GIACENZE: "
            "Description: %(description)s,\n"
            "Weights host_articoli: %(weight_host_articoli)s,\n"
            "Weight host giacenze: %(weight_host_giacenze)s,\n "
            "Quantity: %(quantity)s." % product_info
        )
        res["params"].update(
            {
                "message": contents,
            }
        )
        return res
