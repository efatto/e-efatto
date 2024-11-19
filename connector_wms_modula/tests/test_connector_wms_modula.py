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
        dbsource_name = "Odoo WMS local server"
        dbsource = self.dbsource_model.search([("name", "=", dbsource_name)])
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
                'name': dbsource_name,
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
        res = self.dbsource.execute_mssql(
            sqlquery=sql_text(
                "SELECT RIG_ORDINE, RIG_HOSTINF, RIG_ARTICOLO, RIG_QTAR "
                "FROM IMP_ORDINI_RIGHE WHERE RIG_QTAR!=:RIG_QTAR"),
            sqlparams=dict(RIG_QTAR=0),
            metadata=None,
        )
        return res and res[0] or []

    def test_00_complete_picking_from_sale(self):
        with self.assertRaises(ConnectionSuccessError):
            self.dbsource.connection_test()
        whs_len_records = len(self._execute_select_all_valid_host_liste())
        order_form1 = Form(self.env["sale.order"])
        order_form1.partner_id = self.partner
        order_form1.client_order_ref = "Rif. SO customer"
        with order_form1.order_line.new() as order_line:
            order_line.product_id = self.product1
            order_line.product_uom_qty = 5
            order_line.price_unit = 100
        order1 = order_form1.save()
        order1.action_confirm()
        self.assertEqual(order1.state, 'sale')
        picking1 = order1.picking_ids[0]
        self.assertEqual(len(picking1.move_lines.whs_list_ids), 1)
        if all(x.state == 'assigned' for x in picking1.move_lines):
            self.assertEqual(picking1.state, 'assigned')
        else:
            self.assertEqual(picking1.state, 'waiting')
        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self._execute_select_all_valid_host_liste()
        self.assertEqual(len(whs_records), whs_len_records + 1)
        # RIG_ORDINE, RIG_HOSTINF, RIG_ARTICOLO, RIG_QTAR
        for whs_record in whs_records:
            lista = whs_record[0]
            riga = whs_record[1]
            default_code = whs_record[2]
            qty = whs_record[3]
            self.assertEqual(default_code, order1.order_line.product_id.default_code)
            # if self.product1.default_code == default_code:
            #     self.assertEqual(
            #         self.product1.customer_ids[0].product_code,
            #         product_code
            #     )
            # else:
            #     self.assertEqual(  # FIXME era notEqual
            #         self.product1.customer_ids[0].product_code,
            #         product_code
            #     )
        # check cancel workflow
        whs_lists = picking1.move_lines.whs_list_ids
        self.assertEqual(len(whs_lists), 1)
        whs_list = whs_lists[0]
        self.assertEqual(whs_list.stato, '2')
        if all(x.state == 'assigned' for x in picking1.move_lines):
            self.assertEqual(picking1.state, 'assigned')
        else:
            self.assertEqual(picking1.state, 'waiting')
        picking1.action_cancel()
        self.assertEqual(picking1.state, 'cancel')
        # check whs lists are in stato '3' -> 'Da NON elaborare'
        self.assertEqual(picking1.move_lines.mapped('whs_list_ids.stato'), ['3'])
        # restore picking to assigned state
        picking1.action_back_to_draft()
        picking1.action_confirm()
        picking1.action_assign()
        whs_lists = picking1.move_lines.whs_list_ids.filtered(
            lambda x: x.stato != '3'
        )
        self.assertEqual(len(whs_lists), 1)
        whs_list = whs_lists[0]
        self.assertTrue(whs_list)
        # check whs list is added, and only 1 valid whs list exists
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self._execute_select_all_valid_host_liste()
        self.assertEqual(len(whs_records), whs_len_records + 1)
        # simulate whs work
        lotto = '55A1'
        lotto2 = '55A2'
        lotto3 = '55A3'
        lotto4 = '55A4'
        lotto5 = '55A5'
        set_liste_elaborated_query = \
            "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s, " \
            "Lotto='%s', Lotto2='%s', Lotto3='%s', Lotto4='%s', Lotto5='%s' WHERE " \
            "NumLista = '%s' AND NumRiga = '%s'" % (
                whs_list.qta, lotto, lotto2, lotto3, lotto4, lotto5, whs_list.num_lista,
                whs_list.riga
            )
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=sql_text(set_liste_elaborated_query), sqlparams=None, metadata=None
        )

        whs_select_query = \
            "SELECT Qta, QtaMovimentata, Lotto, Lotto3, Lotto3, Lotto4, Lotto5 " \
            "FROM HOST_LISTE WHERE Elaborato = 4 AND " \
            "NumLista = '%s' AND NumRiga = '%s'" % (
                whs_list.num_lista, whs_list.riga
            )
        result_liste = self.dbsource.execute_mssql(
            sqlquery=sql_text(whs_select_query), sqlparams=None, metadata=None
        )
        self.assertEqual(
            str(result_liste[0]),
            "[(Decimal('5.000'), Decimal('5.000'), '55A1', '55A3', '55A3', '55A4', "
            "'55A5')]")

        self.dbsource.whs_insert_read_and_synchronize_list()

        # check move and picking linked to sale order have changed state to done
        self.assertEqual(picking1.move_lines[0].state, 'assigned')
        if all(x.state == 'assigned' for x in picking1.move_lines):
            self.assertEqual(picking1.state, 'assigned')
        else:
            self.assertEqual(picking1.state, 'waiting')
        picking1.action_assign()
        if all(x.state == 'assigned' for x in picking1.move_lines):
            self.assertEqual(picking1.state, 'assigned')
        else:
            self.assertEqual(picking1.state, 'waiting')
        # check lot info
        self.assertEqual(whs_list.lotto, lotto)
        self.assertEqual(whs_list.lotto2, lotto2)
        self.assertEqual(whs_list.lotto3, lotto3)
        self.assertEqual(whs_list.lotto4, lotto4)
        self.assertEqual(whs_list.lotto5, lotto5)
