# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields


class HyddemoMssqlLog(models.Model):
    _name = "hyddemo.mssql.log"
    _description = "Synchronization with Remote Mssql DB"
    _order = 'ultimo_invio desc'

    ultimo_id = fields.Integer('Last ID in WHS', default=1)
    ultimo_invio = fields.Datetime('Last Processing', readonly=True)
    errori = fields.Text('Log Processing', readonly=True)
    dbsource_id = fields.Many2one(
        'base.external.dbsource',
        'External DB Source Origin',
        readonly=True)
    inventory_id = fields.Many2one(
        'stock.inventory',
        'Created inventory',
        readonly=True)
    hyddemo_mssql_log_line_ids = fields.One2many(
        'hyddemo.mssql.log.line',
        'hyddemo_mssql_log_id',
        'Log lines'
    )


class HyddemoMssqlLogLine(models.Model):
    _name = "hyddemo.mssql.log.line"
    _description = "Mssql Log Line"

    name = fields.Text()
    qty_wrong = fields.Float()
    qty = fields.Float()
    weight = fields.Float()
    weight_wrong = fields.Float()
    product_id = fields.Many2one(
        'product.product')
    type = fields.Selection([
        ('not_found', 'Not found'),
        ('ok', 'Ok'),
        ('mismatch', 'Mismatch'),
        ('service', 'Service'),
    ], 'Type')
    lot = fields.Text()
    hyddemo_mssql_log_id = fields.Many2one(
        'hyddemo.mssql.log')
