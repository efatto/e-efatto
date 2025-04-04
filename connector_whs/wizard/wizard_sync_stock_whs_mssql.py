
from odoo import fields, models


class WizardSyncStockWhsMssql(models.TransientModel):
    _name = "wizard.sync.stock.whs.mssql"
    _description = "Synchronize stock inventory from the Remote Mssql DB to Odoo"

    do_sync = fields.Boolean(
        string="Synchronize stock inventory",
        help="Valid quantities are those found in the remote database.")
    product_id = fields.Many2one("product.product", string="Product to sync")

    @staticmethod
    def _prepare_giacenze_query(i):
        # overridable method
        # respect order of fields retrieved!
        query = ""
        return query

    def apply(self):
        return {
            "type": "ir.actions.act_window_close",
        }
