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

    def _select_wms_liste(self, wms_list, db_type="EXP"):
        return self.dbsource.execute_mssql(
            sqlquery=sql_text(
                f"SELECT RIG_QTAR {', RIG_QTAE' if db_type == 'EXP' else ''} "
                f"FROM {db_type}_ORDINI_RIGHE WHERE "
                "RIG_ORDINE=:RIG_ORDINE AND RIG_HOSTINF=:RIG_HOSTINF"
            ),
            sqlparams=dict(
                RIG_ORDINE=wms_list.num_lista, RIG_HOSTINF=wms_list.riga),
            metadata=None
        )

    def _check_cancel_workflow(self, picking, list_len):
        """
        This method is used to check the re-use of the same whs list linked to the
        picking when this is cancelled, without re-creating a new one.
        """
        whs_lists = picking.mapped("move_lines.whs_list_ids")
        num_liste = whs_lists.mapped('num_lista')
        self.assertEqual(len(whs_lists), list_len)
        self.assertEqual(set(whs_lists.mapped("stato")), {"2"})
        self.assertEqual(set(whs_lists.mapped('qtamov')), {0.0})
        picking.action_assign()
        self.assertEqual(picking.state, "assigned")
        picking.action_cancel()
        # check whs lists are deleted
        self.assertEqual(picking.state, 'cancel')
        self.assertFalse(picking.mapped("move_lines.whs_list_ids"))
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records1 = self.dbsource.execute_mssql(
            sqlquery=sql_text(
                "SELECT RIG_ORDINE, RIG_HOSTINF FROM EXP_ORDINI_RIGHE "
                "WHERE RIG_ORDINE IN :RIG_ORDINE"),
            sqlparams=dict(RIG_ORDINE=num_liste),
            metadata=None,
        )
        self.assertFalse(whs_records1[0], "Exported data from WMS are not deleted!")
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
        self.assertEqual(len(whs_records2), list_len,
                         "There must exist 2 valid WMS records!")
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
        self.assertEqual(len(whs_records), 1)
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
        self.assertEqual(len(whs_records), 1)
        self.simulate_wms_cron({x: x.qta for x in whs_lists})

        result_liste = self._select_wms_liste(whs_lists)
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
        # lists are not processed in Modula now, so do not launch simulate_wms_cron() as
        # it do the whole process (import from Host to Modula, process by user, export
        # from Modula to Host)
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
        self.assertEqual(len(whs_records), 2)
        # simulate whs work: validate first move partially (3 over 5)
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.simulate_wms_cron({x: 3 for x in whs_lists})
        for whs_list in whs_lists:
            result_liste = self._select_wms_liste(whs_list)
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

    def test_02_partial_picking_partial_available_from_sale(self):
        with self.assertRaises(ConnectionSuccessError):
            self.dbsource.connection_test()
        order_form1 = Form(self.env["sale.order"])
        order_form1.partner_id = self.partner
        order_form1.client_order_ref = "Rif. SO customer 2"
        with order_form1.order_line.new() as order_line:
            order_line.product_id = self.product1
            order_line.product_uom_qty = 5
            order_line.price_unit = 100
        with order_form1.order_line.new() as order_line:
            order_line.product_id = self.product2
            order_line.product_uom_qty = 20
            order_line.price_unit = 100
        order1 = order_form1.save()
        order1.action_confirm()
        self.assertEqual(order1.state, 'sale')
        picking = order1.picking_ids[0]
        self.assertEqual(len(picking.mapped('move_lines.whs_list_ids')), 2)
        self.assertEqual(picking.state, 'assigned')

        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        # self.simulate_wms_cron(
        #     {x: x.qta for x in picking.mapped('move_lines.whs_list_ids')})
        whs_records = self.dbsource.execute_mssql(
            sqlquery=sql_text(
                "SELECT RIG_ORDINE, RIG_HOSTINF, RIG_ARTICOLO, RIG_QTAR "
                "FROM IMP_ORDINI_RIGHE WHERE RIG_QTAR!=:RIG_QTAR"),
            sqlparams=dict(RIG_QTAR=0),
            metadata=None,
        )[0]
        self.assertEqual(len(whs_records), 2)
        # check backorder is not created without whs list validation
        res = picking.button_validate()
        Form(self.env[res['res_model']].with_context(res['context'])).save().process()
        # User cannot create backorder if whs list is not processed on whs system
        # TODO: check backorder is created for residual
        self.assertNotEqual(picking.state, 'done')
        self.assertEqual(len(order1.picking_ids), 1)

        whs_lists = picking.mapped("move_lines.whs_list_ids")
        # simulate whs work: partial processing (3 of 5) of product #1
        # and total (20 of 20) of product #2 so it is -4 on warehouse
        self.simulate_wms_cron({
            x: 3 if x.product_id == self.product1 else 20 for x in whs_lists})
        # check whs work is done correctly
        for whs_list in whs_lists:
            result_liste = self._select_wms_liste(whs_list)
            self.assertEqual(
                str(result_liste[0]),
                "[(Decimal('5.000'), Decimal('3.000'))]"
                if whs_list.product_id == self.product1 else
                "[(Decimal('20.000'), Decimal('20.000'))]")

        self.dbsource.whs_insert_read_and_synchronize_list()
        self.simulate_wms_cron(
            {x: x.qta for x in picking.mapped('move_lines.whs_list_ids')})
        # check move and picking linked to sale order have changed state to done
        self.assertEqual(picking.move_lines[0].state, 'assigned')
        self.assertAlmostEqual(picking.move_lines[0].move_line_ids[0].qty_done, 3.0)
        picking.action_assign()
        if all(x.state == 'assigned' for x in picking.move_lines):
            self.assertEqual(picking.state, 'assigned')
        else:
            self.assertEqual(picking.state, 'waiting')
        # check that action_assign run by scheduler do not change state
        self.run_stock_procurement_scheduler()
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')

        # simulate user partial validate of picking and check backorder exist
        backorder_wiz_id = picking.button_validate()['res_id']
        backorder_wiz = self.env['stock.backorder.confirmation'].browse(
            backorder_wiz_id)
        # User cannot create backorder if whs list is not processed on whs system
        # with self.assertRaises(UserError):
        # TODO: check backorder is created for residual
        backorder_wiz.process()

        # Simulate whs user validation
        whs_lists = picking.mapped('move_lines.whs_list_ids')
        # this function do the action_assign() too
        self.dbsource.whs_insert_read_and_synchronize_list()
        # simulate whs work: total process
        self.simulate_wms_cron({
            x: 2 if x.product_id == self.product2 else 3 for x in whs_lists
        })
        backorder_wiz.process()
        self.assertEqual(picking.state, 'done')

        # check back picking is waiting as Odoo qty is not considered
        self.assertEqual(len(order1.picking_ids), 2)
        backorder_picking = order1.picking_ids - picking
        back_whs_list = backorder_picking.mapped('move_lines.whs_list_ids')
        self.assertEqual(backorder_picking.move_lines.mapped('state'), ['assigned'])
        # todo check also a 'partially_available'
        self.assertEqual(backorder_picking.state, 'assigned')

        # todo check whs_list for backorder is created
        self.dbsource.whs_insert_read_and_synchronize_list()
        result_liste = self._select_wms_liste(back_whs_list)
        self.assertFalse(result_liste[0])
        # simulate whs work set done to rest of backorder
        self.simulate_wms_cron({x: 2 for x in back_whs_list})
        result_liste = self._select_wms_liste(back_whs_list)
        self.assertEqual(str(result_liste[0]), "[(Decimal('2.000'), Decimal('2.000'))]")
        self.dbsource.whs_insert_read_and_synchronize_list()
        backorder_picking.button_validate()
        self.assertEqual(backorder_picking.state, 'done')

    def test_03_partial_picking_from_sale(self):
        with self.assertRaises(ConnectionSuccessError):
            self.dbsource.connection_test()
        order_form1 = Form(self.env["sale.order"])
        order_form1.partner_id = self.partner
        order_form1.client_order_ref = "Rif. SO customer 3"
        with order_form1.order_line.new() as order_line:
            order_line.product_id = self.product1
            order_line.product_uom_qty = 5  # 16
            order_line.price_unit = 100
        with order_form1.order_line.new() as order_line:
            order_line.product_id = self.product2
            order_line.product_uom_qty = 10  # 8
            order_line.price_unit = 100
        with order_form1.order_line.new() as order_line:
            order_line.product_id = self.product3
            order_line.product_uom_qty = 20  # 250
            order_line.price_unit = 100
        with order_form1.order_line.new() as order_line:
            order_line.product_id = self.product4
            order_line.product_uom_qty = 20  # 0
            order_line.price_unit = 100
        order1 = order_form1.save()
        order1.action_confirm()
        self.assertEqual(order1.state, 'sale')
        self.assertEqual(order1.mapped('picking_ids.state'), ['assigned'])
        picking = order1.picking_ids[0]
        self.assertEqual(len(picking.mapped('move_lines.whs_list_ids')), 4)

        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self._execute_select_all_valid_host_liste()
        self.assertEqual(len(whs_records), 4)
        # simulate whs work: validate first move totally and second move partially
        whs_lists = picking.mapped('move_lines.whs_list_ids')
        self.simulate_wms_cron({
            x: 0 if x.product_id == self.product3 else 5 for x in whs_lists})
        for whs_list in whs_lists:
            result_liste = self._select_wms_liste(whs_list)
            self.assertEqual(
                str(result_liste[0]),
                "[(Decimal('5.000'), Decimal('5.000'))]"
                if whs_list.product_id == self.product1 else
                "[(Decimal('10.000'), Decimal('5.000'))]"
                if whs_list.product_id == self.product2 else
                "[(Decimal('20.000'), Decimal('0.000'))]"
                if whs_list.product_id == self.product3 else
                "[(Decimal('20.000'), Decimal('5.000'))]")

        self.dbsource.whs_insert_read_and_synchronize_list()

        # check move and picking linked to sale order have changed state to done
        for move_line in picking.move_lines:
            for stock_move_line in move_line.move_line_ids:
                if stock_move_line.product_id in [
                        self.product1, self.product2, self.product4]:
                    self.assertAlmostEqual(stock_move_line.qty_done, 5.0)
                if stock_move_line.product_id == self.product3:
                    self.assertAlmostEqual(stock_move_line.qty_done, 0)
        self.run_stock_procurement_scheduler()
        # check that action_assign run by scheduler do not change state
        # self.assertEqual(picking.state, "confirmed")
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')

        # simulate user partial validate of picking and check backorder exist
        backorder_wiz_id = picking.button_validate()['res_id']
        backorder_wiz = self.env['stock.backorder.confirmation'].browse(
            backorder_wiz_id)
        # User must set correctly quantity as set by WHS user, ignoring qty set
        # automatically by Odoo, so check that error is raised without intervention
        with self.assertRaises(UserError):
            backorder_wiz.process()
        for move_line in picking.move_lines:
            move_line.quantity_done = 5 if move_line.product_id in [
                self.product1, self.product2, self.product4] else 0
        backorder_wiz.process()
        self.assertEqual(picking.state, "done")
        # check backorder whs list has the correct qty
        self.assertEqual(len(order1.picking_ids), 2)
        backorder_picking = order1.picking_ids - picking
        for move_line in backorder_picking.move_lines:
            self.assertAlmostEqual(move_line.whs_list_ids[0].qta, 5 if
                                   move_line.product_id == self.product2 else 20 if
                                   move_line.product_id == self.product3 else 15)

        # Simulate whs user validation
        whs_lists = picking.mapped('move_lines.whs_list_ids')
        # simulate whs work: total process
        self.simulate_wms_cron({x: x.qta for x in whs_lists})

        self.dbsource.whs_insert_read_and_synchronize_list()
        # check whs list for backorder is not created as the first is completed entirely
        # FIXME: what does the note above mean?
        res = self._execute_select_all_valid_host_liste()
        self.assertEqual(len(res), 3)
        backorder_picking.action_assign()

    def test_04_unlink_sale_order(self):
        with self.assertRaises(ConnectionSuccessError):
            self.dbsource.connection_test()
        order_form1 = Form(self.env["sale.order"])
        order_form1.partner_id = self.partner
        order_form1.client_order_ref = "Rif. SO customer 4"
        with order_form1.order_line.new() as order_line:
            order_line.product_id = self.product1
            order_line.product_uom_qty = 5
            order_line.price_unit = 100
        with order_form1.order_line.new() as order_line:
            order_line.product_id = self.product2
            order_line.product_uom_qty = 5
            order_line.price_unit = 100
        order1 = order_form1.save()
        order1.action_confirm()
        self.assertEqual(order1.state, "sale")
        self.assertEqual(len(order1.picking_ids), 1)
        picking = order1.picking_ids
        picking.action_assign()
        self.assertEqual(picking.state, "assigned")
        picking = order1.picking_ids[0]
        self.assertEqual(len(picking.mapped('move_lines.whs_list_ids')), 2)

        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            2,
        )
        # controlla che le liste whs siano annullate (impostate con Qta=0)
        order1.action_cancel()
        # insert lists in WHS: this has to be invoked before every sql call!
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            0,
        )
        self.assertFalse(order1.mapped("picking_ids.move_lines.whs_list_ids"))
        order1.action_draft()
        order1.action_confirm()
        picking = order1.picking_ids.filtered(lambda x: x.state != 'cancel')
        self.assertEqual(picking.mapped('move_lines.whs_list_ids.stato'), ['1', '1'])
        # insert lists in WHS: this has to be invoked before every sql call!
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            2,
        )
        # self.run_stock_procurement_scheduler()
        picking.action_assign()
        self.assertEqual(picking.state, "assigned")
        whs_lists = picking.mapped("move_lines.whs_list_ids")
        # todo it's not possibile to simulate a work in progress from WHS user, as there
        #  are only done lists in EXP_ORDINI* tables afaik (check it)
        self.simulate_wms_cron({x: x.qta for x in whs_lists})
        # check an order done cannot be cancelled, even if it is not already synced by
        # Odoo cron
        with self.assertRaises(UserError):
            order1.action_cancel()
        # Check product added to sale order after confirmation create new whs lists
        # adding product to an existing open picking
        order_form2 = Form(order1)
        with order_form2.order_line.new() as order_line:
            order_line.product_id = self.product4
            order_line.product_uom_qty = 5
            order_line.price_unit = 100
        order1 = order_form2.save()
        pickings = order1.picking_ids.filtered(lambda x: x.state == "assigned")
        pickings.action_assign()
        new_product_move_line_ids = order1.picking_ids.mapped('move_lines').filtered(
            lambda x: x.product_id == self.product4
        )
        self.assertTrue(new_product_move_line_ids.mapped("whs_list_ids"))
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            1,
        )

        # test change qty of sale order line is forbidden
        with self.assertRaises(UserError):
            order1.order_line[0].write({"product_uom_qty": 17})

    def test_05_repair(self):
        with self.assertRaises(ConnectionSuccessError):
            self.dbsource.connection_test()

        repair_form = Form(self.env["repair.order"])
        repair_form.product_id = self.product1
        repair_form.product_uom = self.product1.uom_id
        repair_form.partner_id = self.partner
        repair_form.product_qty = 1
        repair_form.location_id = self.env.ref("stock.stock_location_stock")
        with repair_form.operations.new() as repair_line_form:
            repair_line_form.product_id = self.product2
            repair_line_form.name = "Add product"
            repair_line_form.type = "add"
            repair_line_form.product_uom_qty = 5
            repair_line_form.product_uom = self.product2.uom_id
            repair_line_form.price_unit = 5
            repair_line_form.location_id = self.env.ref("stock.stock_location_stock")
            repair_line_form.location_dest_id = self.manufacture_location
        with repair_form.operations.new() as repair_line_form:
            repair_line_form.product_id = self.product3
            repair_line_form.name = "Add product"
            repair_line_form.type = "add"
            repair_line_form.product_uom_qty = 3
            repair_line_form.product_uom = self.product3.uom_id
            repair_line_form.price_unit = 5
            repair_line_form.location_id = self.env.ref("stock.stock_location_stock")
            repair_line_form.location_dest_id = self.manufacture_location
        repair = repair_form.save()
        repair.action_repair_confirm()
        self.assertEqual(repair.state, "confirmed",
                         'Repair order should be in "Confirmed" state.')
        repair.action_repair_start()
        self.assertEqual(repair.state, "under_repair",
                         'Repair order should be in "Under_repair" state.')
        repair.action_repair_end()
        self.assertEqual(repair.state, "done",
                         'Repair order should be in "Done" state.')
        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            2,
        )

        # simulate whs work: partial processing of product #2
        # and total of product #3
        whs_lists = repair.mapped('operations.move_id.whs_list_ids')
        self.simulate_wms_cron({
            x: 2 if x.product_id == self.product2 else 3 for x in whs_lists
        })
        for whs_list in whs_lists:
            result_liste = self._select_wms_liste(whs_list)
            self.assertEqual(
                str(result_liste[0]),
                "[(Decimal('5.000'), Decimal('2.000'))]"
                if whs_list.product_id == self.product2 else
                "[(Decimal('3.000'), Decimal('3.000'))]")

    def test_06_purchase(self):
        with self.assertRaises(ConnectionSuccessError):
            self.dbsource.connection_test()
        purchase_form = Form(self.env["purchase.order"])
        purchase_form.partner_id = self.partner
        with purchase_form.order_line.new() as po_line:
            po_line.product_id = self.product2
            po_line.product_qty = 20
            po_line.product_uom = self.product2.uom_po_id
            po_line.name = self.product2.name
            po_line.price_unit = 100
            po_line.date_planned = fields.Datetime.today() + relativedelta(month=1)
        with purchase_form.order_line.new() as po_line:
            po_line.product_id = self.product3
            po_line.product_qty = 3
            po_line.product_uom = self.product3.uom_po_id
            po_line.name = self.product3.name
            po_line.price_unit = 100
            po_line.date_planned = fields.Datetime.today() + relativedelta(month=1)
        purchase = purchase_form.save()
        purchase.button_approve()
        self.assertEqual(
            purchase.state, 'purchase', 'Purchase state should be "Purchase"')
        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            2,
        )

        # simulate whs work: partial processing of product #2
        # and total of product #3
        whs_lists = purchase.mapped('picking_ids.move_lines.whs_list_ids')
        self.simulate_wms_cron({
            x: 2 if x.product_id == self.product2 else 3 for x in whs_lists})
        for whs_list in whs_lists:
            result_liste = self._select_wms_liste(whs_list)
            self.assertEqual(
                str(result_liste[0]),
                "[(Decimal('20.000'), Decimal('2.000'))]"
                if whs_list.product_id == self.product2 else
                "[(Decimal('3.000'), Decimal('3.000'))]")
        self.dbsource.whs_insert_read_and_synchronize_list()
        # simulate user partial validate of picking and check backorder exist
        picking = purchase.picking_ids[0]
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        backorder_wiz_id = picking.button_validate()['res_id']
        backorder_wiz = self.env['stock.backorder.confirmation'].browse(
            backorder_wiz_id)
        backorder_wiz.process()
        self.assertEqual(picking.state, 'done')

        # check back picking is waiting as waiting for WHS work
        self.assertEqual(len(purchase.picking_ids), 2)
        backorder_picking = purchase.picking_ids - picking
        # self.run_stock_procurement_scheduler()
        backorder_picking.action_assign()
        self.assertEqual(backorder_picking.state, "assigned")

        # check whs_list for backorder is created
        self.dbsource.whs_insert_read_and_synchronize_list()
        back_whs_list = backorder_picking.mapped('move_lines.whs_list_ids')
        result_liste = self._select_wms_liste(back_whs_list, "IMP")
        self.assertEqual(str(result_liste[0]), "[(Decimal('18.000'),)]")
        # TODO check cancel workflow without action_assign that create whs list anyway
        self._check_cancel_workflow(backorder_picking, 1)
        backorder_picking.action_assign()
        back_whs_list = backorder_picking.mapped('move_lines.whs_list_ids')
        # DO NOT simulate whs work set done to rest of backorder
        # self.simulate_wms_cron({x: 18 for x in back_whs_list})
        self.dbsource.whs_insert_read_and_synchronize_list()
        backorder_picking.button_validate()
        self.assertEqual(backorder_picking.state, "assigned")
        self.assertFalse(
            all(
                whs_list.stato == "3"
                for whs_list in backorder_picking.move_lines.whs_list_ids
            )
        )
        # Check product added to purchase order after confirm create whs list with
        # different date_planned which create a new picking (as this module depends on
        # purchase_delivery_split_date)
        purchase_form = Form(purchase)
        with purchase_form.order_line.new() as po_line:
            po_line.product_id = self.product4
            po_line.product_qty = 20
            po_line.product_uom = self.product4.uom_po_id
            po_line.name = self.product4.name
            po_line.price_unit = 100
            po_line.date_planned = fields.Datetime.today() + relativedelta(month=2)
        purchase_form.save()
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            2,
        )
        # Check product added to purchase order after confirmation create new whs lists
        # adding product to an existing open picking
        purchase_form = Form(purchase)
        with purchase_form.order_line.new() as po_line:
            po_line.product_id = self.product5
            po_line.product_qty = 20
            po_line.product_uom = self.product5.uom_po_id
            po_line.name = self.product5.name
            po_line.price_unit = 100
            po_line.date_planned = fields.Datetime.today() + relativedelta(month=2)
        with purchase_form.order_line.new() as po_line:
            po_line.product_id = self.product5
            po_line.product_qty = 20
            po_line.product_uom = self.product5.uom_po_id
            po_line.name = self.product5.name
            po_line.price_unit = 100
            po_line.date_planned = fields.Datetime.today() + relativedelta(month=2)
        purchase_form.save()
        # pickings linked to purchase order change state to assigned when a product is
        # added o changed
        pickings = purchase.picking_ids.filtered(lambda x: x.state == "assigned")
        pickings.action_assign()  # aka "Controlla disponibilità"
        new_product_move_line_ids = purchase.picking_ids.mapped('move_lines').filtered(
            lambda x: x.product_id == self.product5
        )
        self.assertTrue(new_product_move_line_ids.mapped("whs_list_ids"))
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            4,
        )

        # test qty change on purchase order line, which create a new line with increased
        # qty on picking
        po_line_to_change = purchase.order_line.filtered(
            lambda x: x.product_id == self.product5
        )[-1]
        po_line_to_change.write({"product_qty": 27})
        pickings = purchase.picking_ids.filtered(
            lambda x: x.state == "assigned"
        )
        pickings.action_assign()
        po_whs_list = po_line_to_change.mapped("move_ids.whs_list_ids").filtered(
            lambda x: x.qta == 7
        )
        self.dbsource.whs_insert_read_and_synchronize_list()
        result_liste = self._select_wms_liste(po_whs_list, db_type="IMP")
        # whs list is created for the increased qty
        self.assertEqual(str(result_liste[0]), "[(Decimal('7.000'),)]")
