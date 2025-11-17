# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class HyddemoMssqlLog(models.Model):
    _name = "hyddemo.mssql.log"
    _description = "Synchronization with Remote Mssql DB"
    _order = "ultimo_invio desc"

    ultimo_id = fields.Integer("Last ID in WMS", default=1)
    ultimo_invio = fields.Datetime("Last Processing", readonly=True)
    errori = fields.Text("Log WMS", readonly=True)
    dbsource_id = fields.Many2one(
        "base.external.dbsource", "External DB Source Origin", readonly=True
    )
    inventory_id = fields.Many2one(
        "stock.inventory", "Created inventory", readonly=True
    )
    hyddemo_mssql_log_line_ids = fields.One2many(
        "hyddemo.mssql.log.line", "hyddemo_mssql_log_id", "Log lines"
    )


class HyddemoMssqlLogLine(models.Model):
    _name = "hyddemo.mssql.log.line"
    _description = "Mssql Log Line"

    name = fields.Text()
    product_name = fields.Text()
    qty_wrong = fields.Float(
        string="Odoo Q.ty (wrong)",
        help="This quantity is assumed as wrong and overriden by WMS quantity if "
        "'Synchronize stock inventory' is set.",
    )
    qty = fields.Float(string="WMS Q.ty")
    weight = fields.Float(string="WMS Weight")
    weight_wrong = fields.Float(
        string="Odoo Weight (wrong)",
        help="This weight is assumed as wrong and overriden by WMS weight if "
        "'Synchronize stock inventory' is set.",
    )
    product_id = fields.Many2one("product.product")
    type = fields.Selection(
        [
            ("not_found", "Not found"),
            ("ok", "Ok"),
            ("mismatch", "Mismatch"),
            ("service", "Service"),
            ("info", "Info"),
        ],
        "Type",
    )
    lot = fields.Text()
    hyddemo_mssql_log_id = fields.Many2one("hyddemo.mssql.log")
