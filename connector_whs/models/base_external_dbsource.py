# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models
from odoo.tools.config import config as system_base_config


class BaseExternalDbsource(models.Model):
    _inherit = "base.external.dbsource"

    @api.depends("location_id")
    def _compute_warehouse(self):
        for dbsource in self:
            if dbsource.location_id:
                warehouse = self.env["stock.warehouse"].search(
                    [("lot_stock_id", "=", dbsource.location_id.id)]
                )
                if warehouse:
                    dbsource.warehouse_id = warehouse[0]

    location_id = fields.Many2one("stock.location", "Location linked to WHS")
    warehouse_id = fields.Many2one(
        compute=_compute_warehouse,
        comodel_name="stock.warehouse",
        string="Warehouse linked to WHS",
    )
    conn_string_sandbox = fields.Text("Connection string sandbox")
    clean_days_limit = fields.Integer(
        string="Days to keep active lists",
        default=365,
        help="Clean whs lists and db list older than this number of days.",
    )
    active = fields.Boolean(string="Active", default=True)

    @api.depends("conn_string", "conn_string_sandbox", "password")
    def _compute_conn_string_full(self):
        if not system_base_config.get("running_env"):
            system_base_config["running_env"] = "test"
        server_running_state = system_base_config.get("running_env")
        for record in self:
            conn_string = record.conn_string
            if server_running_state != "prod":
                conn_string = record.conn_string_sandbox
            if record.password:
                if "%s" not in conn_string:
                    pwd_string = getattr(
                        record,
                        "PWD_STRING_%s" % record.connector.upper(),
                        record.PWD_STRING,
                    )
                    conn_string += pwd_string
                record.conn_string_full = conn_string % record.password
            else:
                record.conn_string_full = conn_string

    def whs_update_products(self):
        for dbsource in self:
            self.env["hyddemo.mssql.log"].whs_update_products(dbsource.id)
        return True

    def whs_insert_read_and_synchronize_list(self):
        self.env["hyddemo.mssql.log"].whs_insert_list_to_elaborate(self.id)
        # commit to exclude rollback as mssql wouldn't be rollbacked too
        # without this commit, record will be inserted multiple times too
        self.env.cr.commit()  # pylint: disable=E8102
        self.env["hyddemo.mssql.log"].whs_read_and_synchronize_list(self.id)
        self.env.cr.commit()  # pylint: disable=E8102

    def whs_check_lists(self):
        for dbsource in self:
            self.env["hyddemo.mssql.log"].whs_check_list_state(dbsource.id)
        return True

    def whs_check_list_not_passed(self):
        for dbsource in self:
            self.env["hyddemo.mssql.log"].whs_check_list_not_passed(dbsource.id)
        return True

    @api.model
    def _cron_whs_clean_lists(self):
        for dbsource in self.search([]):
            self.env["hyddemo.mssql.log"].whs_clean_lists(dbsource.id)
        return True

    @api.model
    def _cron_whs_synchronize(self):
        for dbsource in self.search([]):
            dbsource.whs_insert_read_and_synchronize_list()

    @api.model
    def _cron_whs_synchronize_stock(self, do_sync=False):
        for dbsource in self.search([]):
            self.env["hyddemo.mssql.log"].whs_update_products(dbsource.id)
            wizard_obj = self.env["wizard.sync.stock.whs.mssql"]
            wizard_vals = wizard_obj.default_get(["do_sync"])
            wizard_vals.update(do_sync=do_sync)
            wizard = wizard_obj.with_context(
                active_ids=dbsource.ids, active_model="base.external.dbsource"
            ).create([wizard_vals])
            wizard.apply()

    def whs_sync_stock(self):
        self.ensure_one()
        wizard = self.env.ref("connector_whs.view_wizard_sync_stock_whs_mssql", False)
        return {
            "name": "Synchronize stock inventory with Remote Mssql DB",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "views": [(wizard.id, "form")],
            "view_id": wizard.id,
            "target": "new",
            "res_model": "wizard.sync.stock.whs.mssql",
        }
