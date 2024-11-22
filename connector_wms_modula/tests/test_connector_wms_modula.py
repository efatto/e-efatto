import os
from odoo import fields
from odoo.addons.base_external_dbsource.exceptions import ConnectionSuccessError
from odoo.tests import tagged
from odoo.tests.common import Form
from odoo.addons.connector_whs.tests.test_connector_wms import CommonConnectorWMS
from ..models.hyddemo_whs_liste import tipo_operazione_dict
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
            sqlquery=sql_text("DELETE FROM IMP_ORDINI_RIGHE"),
            sqlparams=None, metadata=None
        )
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=sql_text("DELETE FROM IMP_ORDINI"), sqlparams=None, metadata=None
        )
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=sql_text("DELETE FROM EXP_ORDINI_RIGHE"),
            sqlparams=None, metadata=None
        )
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=sql_text("DELETE FROM EXP_ORDINI"), sqlparams=None, metadata=None
        )

    def _check_cancel_workflow(self, picking, list_len):
        """
        This method is used to check the re-use of the same whs list linked to the
        picking when this is cancelled, without re-creating a new one.
        """
        whs_lists = picking.mapped("move_lines.whs_list_ids")
        whs_records = self.dbsource.execute_mssql(
            sqlquery=sql_text(
                "SELECT RIG_ORDINE, RIG_HOSTINF FROM EXP_ORDINI_RIGHE "
                "WHERE RIG_ORDINE IN :RIG_ORDINE"),
            sqlparams=dict(
                RIG_ORDINE=whs_lists.mapped("num_lista")),
            metadata=None,
        )[0]

        self.assertEqual(len(whs_lists), list_len)
        self.assertEqual(set(whs_lists.mapped("stato")), {"2"})
        self.assertEqual(set(whs_lists.mapped('qtamov')), {0.0})
        picking.action_assign()
        self.assertEqual(picking.state, "assigned")
        picking.action_cancel()
        # check whs lists are in stato '3' -> 'Da NON elaborare'
        self.assertEqual(picking.state, 'cancel')
        self.assertEqual(set(whs_lists.mapped('stato')), {'3'})
        self.assertEqual(set(whs_lists.mapped('qtamov')), {0.0})
        self.dbsource.whs_insert_read_and_synchronize_list()
        # self.simulate_wms_cron(picking.move_lines.mapped('whs_list_ids'))
        whs_records1 = self.dbsource.execute_mssql(
            sqlquery=sql_text(
                "SELECT RIG_ORDINE, RIG_HOSTINF FROM EXP_ORDINI_RIGHE "
                "WHERE RIG_ORDINE IN :RIG_ORDINE"),
            sqlparams=dict(
                RIG_ORDINE=whs_lists.mapped("num_lista")),
            metadata=None,
        )[0]
        # todo self.assertFalse(whs_records1, "Exported data from WMS are not deleted!")
        # restore picking to assigned state
        picking.action_back_to_draft()
        picking.action_confirm()
        if picking.sale_id:
            picking.action_assign()
        valid_whs_lists = picking.mapped("move_lines.whs_list_ids").filtered(
            lambda x: x.stato != "3"
        )
        self.assertEqual(len(valid_whs_lists), list_len)
        # check new whs lists are present
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records2 = self.dbsource.execute_mssql(
            sqlquery=sql_text(
                "SELECT RIG_ORDINE, RIG_HOSTINF FROM IMP_ORDINI_RIGHE "
                "WHERE RIG_ORDINE IN :RIG_ORDINE"),
            sqlparams=dict(
                RIG_ORDINE=valid_whs_lists.mapped("num_lista")),
            metadata=None,
        )[0]
        # 2 whs lists valid
        self.assertEqual(len(whs_records2), len(whs_records),
                         "There must be 2 valid WMS records!")
        return valid_whs_lists

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

    def simulate_wms_cron(self, whs_lists_dict):
        # simulate WMS Modula work: create EXP_ORDINI* and delete IMP_ORDINI*
        whs_lists = self.env["hyddemo.whs.liste"]
        for whs_list in whs_lists_dict:
            whs_lists |= whs_list
        for num_lista in set(whs_lists.mapped("num_lista")):
            current_whs_lists = whs_lists.filtered(lambda x: x.num_lista == num_lista)
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(
                    "INSERT INTO EXP_ORDINI "
                    "(ORD_ORDINE, ORD_TIPOOP, ORD_DES) VALUES "
                    "(:ORD_ORDINE, :ORD_TIPOOP, :ORD_DES)"),
                sqlparams=dict(
                    ORD_ORDINE=num_lista,
                    ORD_TIPOOP=tipo_operazione_dict[current_whs_lists[0].tipo],
                    ORD_DES=current_whs_lists[0].riferimento[:50]
                    if current_whs_lists[0].riferimento else '',
                ), metadata=None
            )
            for whs_list in current_whs_lists:
                self.dbsource.with_context(no_return=True).execute_mssql(
                    sqlquery=sql_text(
                        "INSERT INTO EXP_ORDINI_RIGHE "
                        "(RIG_ORDINE, RIG_HOSTINF, RIG_ARTICOLO, RIG_QTAR, RIG_QTAE) "
                        "VALUES "
                        "(:RIG_ORDINE, :RIG_HOSTINF, :RIG_ARTICOLO, :RIG_QTAR, "
                        ":RIG_QTAE)"
                    ),
                    sqlparams=dict(
                        RIG_ORDINE=whs_list.num_lista,
                        RIG_HOSTINF=whs_list.riga,
                        RIG_ARTICOLO=whs_list.product_id.default_code[:50] if
                        whs_list.product_id.default_code
                        else 'prodotto %s senza codice' % whs_list.product_id.id,
                        RIG_QTAR=whs_list.qta,
                        RIG_QTAE=whs_lists_dict[whs_list],
                    ),
                    metadata=None
                )
        for num_lista in set(whs_lists.mapped("num_lista")):
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(
                    "DELETE FROM IMP_ORDINI_RIGHE WHERE RIG_ORDINE=:RIG_ORDINE"
                ),
                sqlparams=dict(RIG_ORDINE=num_lista), metadata=None
            )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(
                    "DELETE FROM IMP_ORDINI WHERE ORD_ORDINE=:ORD_ORDINE"
                ), sqlparams=dict(ORD_ORDINE=num_lista), metadata=None
            )

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
            default_code = whs_record[2]
            qty = whs_record[3]
            self.assertEqual(default_code, order1.order_line.product_id.default_code)
            self.assertEqual(qty, order1.order_line.product_uom_qty)
            self.assertEqual(qty, picking1.move_lines.whs_list_ids.qta)
            self.assertEqual(lista, picking1.move_lines.whs_list_ids.num_lista)
        # check cancel workflow
        whs_lists = picking1.move_lines.whs_list_ids
        self.assertEqual(len(whs_lists), 1)
        self.assertEqual(whs_lists.stato, '2')
        if all(x.state == 'assigned' for x in picking1.move_lines):
            self.assertEqual(picking1.state, 'assigned')
        else:
            self.assertEqual(picking1.state, 'waiting')
        picking1.action_cancel()
        self.assertEqual(picking1.state, 'cancel')
        # check whs lists are unlinked (only with a working WMS software they could be
        # in stato '3' -> 'Da NON elaborare' after elaboration)
        self.assertFalse(picking1.move_lines.mapped('whs_list_ids'))
        # restore picking to assigned state
        picking1.action_back_to_draft()
        picking1.action_confirm()
        picking1.action_assign()
        whs_lists = picking1.move_lines.whs_list_ids.filtered(
            lambda x: x.stato != '3'
        )
        self.assertEqual(len(whs_lists), 1)
        # check whs list is added, and only 1 valid whs list exists
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self._execute_select_all_valid_host_liste()
        self.assertEqual(len(whs_records), whs_len_records + 1)
        self.simulate_wms_cron({x: x.qta for x in whs_lists})

        result_liste = self.dbsource.execute_mssql(
            sqlquery=sql_text(
                "SELECT RIG_QTAR, RIG_QTAE "
                "FROM EXP_ORDINI_RIGHE WHERE "
                "RIG_ORDINE=:RIG_ORDINE AND RIG_HOSTINF=:RIG_HOSTINF"
            ), sqlparams=dict(
                RIG_ORDINE=whs_lists.num_lista,
                RIG_HOSTINF=whs_lists.riga,
            ), metadata=None
        )
        self.assertEqual(
            str(result_liste[0]),
            "[(Decimal('5.000'), Decimal('5.000'))]")

        self.dbsource.whs_insert_read_and_synchronize_list()

        # check move and picking linked to sale order have changed state to done
        self.assertEqual(picking1.move_lines[0].state, 'assigned')
        self.assertEqual(picking1.state, 'assigned')

    def test_01_partial_picking_from_sale(self):
        with self.assertRaises(ConnectionSuccessError):
            self.dbsource.connection_test()

        whs_len_records = len(self._execute_select_all_valid_host_liste())
        order_form1 = Form(self.env["sale.order"])
        order_form1.partner_id = self.partner
        order_form1.client_order_ref = "Rif. SO customer 1"
        with order_form1.order_line.new() as order_line:
            order_line.product_id = self.product1
            order_line.product_uom_qty = 5
            order_line.price_unit = 100
        with order_form1.order_line.new() as order_line:
            order_line.product_id = self.product1
            order_line.product_uom_qty = 5
            order_line.price_unit = 100
        order1 = order_form1.save()
        order1.action_confirm()
        self.assertEqual(order1.state, 'sale')
        for picking in order1.picking_ids:
            if all(x.state == 'assigned' for x in picking.move_lines):
                self.assertEqual(picking.state, 'assigned')
            else:
                self.assertEqual(picking.state, 'waiting')
        picking = order1.picking_ids[0]
        self.assertEqual(len(picking.mapped('move_lines.whs_list_ids')), 2)
        self.assertEqual(
            len(set(picking.mapped("move_lines.whs_list_ids.num_lista"))), 1
        )

        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.simulate_wms_cron(
            {x: x.qta for x in picking.mapped('move_lines.whs_list_ids')})
        whs_records = self.dbsource.execute_mssql(
            sqlquery=sql_text(
                "SELECT RIG_ORDINE, RIG_HOSTINF, RIG_ARTICOLO, RIG_QTAR, RIG_QTAE "
                "FROM EXP_ORDINI_RIGHE WHERE RIG_QTAR!=:RIG_QTAR"),
            sqlparams=dict(RIG_QTAR=0),
            metadata=None,
        )[0]
        self.assertEqual(len(whs_records), 2)  # number is exactly record to read
        self.assertEqual(set(picking.mapped('move_lines.whs_list_ids.stato')), {'2'})
        whs_lists = self._check_cancel_workflow(picking, 2)
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self.dbsource.execute_mssql(
            sqlquery=sql_text(
                "SELECT RIG_ORDINE, RIG_HOSTINF FROM IMP_ORDINI_RIGHE "
                "WHERE RIG_QTAR!=:RIG_QTAR"),
            sqlparams=dict(RIG_QTAR=0),
            metadata=None,
        )[0]
        self.assertEqual(len(whs_records), whs_len_records + 2)
        # simulate whs work: validate first move partially (3 over 5)
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.simulate_wms_cron({x: 3 for x in whs_lists})
        for whs_list in whs_lists:
            result_liste = self.dbsource.execute_mssql(
                sqlquery=sql_text(
                    "SELECT RIG_QTAR, RIG_QTAE "
                    "FROM EXP_ORDINI_RIGHE WHERE "
                    "RIG_ORDINE=:RIG_ORDINE AND RIG_HOSTINF=:RIG_HOSTINF"
                ),
                sqlparams=dict(
                    RIG_ORDINE=whs_list.num_lista, RIG_HOSTINF=whs_list.riga),
                metadata=None
            )
            self.assertIn("[(Decimal('5.000'), Decimal('3.000'))]",
                          str(result_liste))
        self.dbsource.whs_insert_read_and_synchronize_list()
        # check move and picking linked to sale order have changed state to done
        self.assertEqual(set(picking.move_lines.mapped('state')), {'assigned'})
        self.assertAlmostEqual(picking.move_lines[0].move_line_ids[0].qty_done, 3.0)
        self.assertEqual(picking.state, 'assigned')

        # simulate user partial validate of picking and check backorder exist
        backorder_wiz_id = picking.button_validate()['res_id']
        backorder_wiz = self.env['stock.backorder.confirmation'].browse(
            backorder_wiz_id)
        # Create backorder: 1 whs list of 2 is partially processed
        backorder_wiz.process()
        backorder_picking = order1.picking_ids - picking
        # Simulate whs user validation
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_lists = backorder_picking.mapped("move_lines.whs_list_ids").filtered(
            lambda x: x.stato != "3"
        )
        # simulate whs work: total process
        self.simulate_wms_cron({x: x.qta for x in whs_lists})

        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertFalse(
            self._execute_select_all_valid_host_liste(),
            "Imported lists are not deleted!",
        )

        # check backorder picking is waiting for whs process
        self.assertEqual(len(order1.picking_ids), 2)
        self.assertEqual(backorder_picking.state, 'assigned')
        self.assertEqual(backorder_picking.move_lines[0].state, 'assigned')
