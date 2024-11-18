
from odoo.tests import tagged
from odoo.addons.connector_whs.tests.test_connector_wms import TestConnectorWMS
from sqlalchemy import text as sql_text

connection_string = "connection_wms_modula.txt"

@tagged("-standard", "test_wms")
class TestConnectorWmsModula(TestConnectorWMS):
    def _clean_db(self):
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
        #     sqlquery=sql_text("SELECT * FROM HOST_LISTE WHERE Qta!=:Qta"),
        #     sqlparams=dict(Qta=0),
        #     metadata=None,
        # )[0]
        return []
