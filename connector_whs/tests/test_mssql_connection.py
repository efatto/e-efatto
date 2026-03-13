# Copyright 2024 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
from odoo.tests import tagged
from .test_connector_wms import CommonConnectorWMS

@tagged("-standard", "test_mssql_whs")
class TestMssqlConnection(CommonConnectorWMS):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Leggi la stringa di connessione dal file
        conn_file = os.path.expanduser("~/connection_wms_whs.txt")
        if not os.path.exists(conn_file):
            raise FileNotFoundError(f"File {conn_file} non trovato")
        
        with open(conn_file, 'r') as f:
            conn_string = f.read().strip()
        
        # Cerca o crea un dbsource per il test
        cls.dbsource = cls.dbsource_model.search([('name', '=', 'Test MSSQL WHS')], limit=1)
        if not cls.dbsource:
            cls.dbsource = cls.dbsource_model.create({
                'name': 'Test MSSQL WHS',
                'connector': 'mssql',
                'conn_string_sandbox': conn_string,
                'password': '',  # La password dovrebbe essere già nel file se è un URI completo o gestita diversamente
            })
        else:
            cls.dbsource.write({'conn_string_sandbox': conn_string})

    def test_01_connection(self):
        """Verifica la connessione al server MSSQL"""
        # Il metodo connection_test() solitamente solleva eccezioni se fallisce
        res = self.dbsource.connection_test()
        self.assertTrue(res, "La connessione al database MSSQL è fallita")
