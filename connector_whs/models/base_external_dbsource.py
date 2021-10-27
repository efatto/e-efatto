# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api
from odoo.tools.config import config as system_base_config


class BaseExternalDbsource(models.Model):
    _inherit = "base.external.dbsource"

    @api.multi
    @api.depends('location_id')
    def _compute_warehouse(self):
        for dbsource in self:
            if dbsource.location_id:
                warehouse = self.env['stock.warehouse'].search([
                    ('lot_stock_id', '=', dbsource.location_id.id)
                ])
                if warehouse:
                    dbsource.warehouse_id = warehouse[0]

    location_id = fields.Many2one(
        'stock.location', 'Location linked to WHS')
    warehouse_id = fields.Many2one(
        compute=_compute_warehouse,
        comodel_name='stock.warehouse',
        string='Warehouse linked to WHS')
    conn_string_sandbox = fields.Text('Connection string sandbox')

    @api.multi
    @api.depends('conn_string', 'conn_string_sandbox', 'password')
    def _compute_conn_string_full(self):
        if not system_base_config.get("running_env"):
            system_base_config["running_env"] = "test"
        server_running_state = system_base_config.get("running_env")
        for record in self:
            conn_string = record.conn_string
            if server_running_state != "prod":
                conn_string = record.conn_string_sandbox
            if record.password:
                if '%s' not in conn_string:
                    pwd_string = getattr(
                        record,
                        'PWD_STRING_%s' % record.connector.upper(),
                        record.PWD_STRING,
                    )
                    conn_string += pwd_string
                record.conn_string_full = conn_string % record.password
            else:
                record.conn_string_full = conn_string

    @api.multi
    def whs_update_products(self):
        for dbsource in self:
            self.env['hyddemo.mssql.log'].whs_update_products(
                dbsource.id
            )
        return True

    @api.multi
    def whs_insert_read_and_synchronize_list(self):
        for dbsource in self:
            self.env['hyddemo.mssql.log'].whs_insert_list_to_elaborate(
                dbsource.id
            )
        return True

    @api.model
    def _cron_whs_synchronize(self):
        for dbsource in self.search([]):
            dbsource.whs_insert_read_and_synchronize_list()

    @api.multi
    def whs_sync_stock(self):
        self.ensure_one()
        wizard = self.env.ref('connector_whs.view_wizard_sync_stock_whs_mssql', False)
        return {
            'name': "Synchronize stock inventory with Remote Mssql DB",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(wizard.id, 'form')],
            'view_id': wizard.id,
            'target': 'new',
            'res_model': "wizard.sync.stock.whs.mssql",
        }
