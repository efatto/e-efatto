import os
from odoo import fields
from odoo.addons.base_external_dbsource.exceptions import ConnectionSuccessError
from odoo.tests import tagged
from odoo.tests.common import Form
from odoo.addons.connector_whs.tests.test_connector_wms import CommonConnectorWMS
from odoo.exceptions import UserError
from odoo.tools import relativedelta
from sqlalchemy import text as sql_text


@tagged("-standard", "test_wms")
class TestConnectorWmsModula(CommonConnectorWMS):
    def setUp(self):
        super().setUp()
        dbsource = self.dbsource_model.search([("name", "=", "Odoo WMS local server")])
        if not dbsource:
            conn_file = os.path.join(
                os.path.expanduser('~'),
                "connection_wms_modula.txt"
            )
            if not os.path.isfile(conn_file):
                raise UserError("Missing connection string!")
            with open(conn_file, 'r') as file:
                conn_string = file.read().replace('\n', '')
            dbsource = self.dbsource_model.create({
                'name': 'Odoo WHS local server',
                'conn_string_sandbox': conn_string,
                'connector': 'mssql',
                'location_id': self.env.ref('stock.stock_location_stock').id,
            })
        self.dbsource = dbsource
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=sql_text("DELETE FROM IMP_ORDINI"), sqlparams=None, metadata=None
        )
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=sql_text("DELETE FROM IMP_ORDINI_RIGHE"),
            sqlparams=None, metadata=None
        )

    def _execute_select_all_valid_host_liste(self):
        # insert lists in WHS: this has to be invoked before every sql call!
        self.dbsource.whs_insert_read_and_synchronize_list()
        # res = self.dbsource.execute_mssql(
        #     sqlquery=sql_text("SELECT * FROM IMP_ORDINI_RIGHE WHERE Qta!=:Qta"),
        #     sqlparams=dict(Qta=0),
        #     metadata=None,
        # )[0]
        return []
