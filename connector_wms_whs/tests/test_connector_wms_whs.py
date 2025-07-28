import os

from odoo import _, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import Form, tagged
from odoo.tools import relativedelta

from odoo.addons.connector_whs.models.base_external_dbsource import clean_sql_text
from odoo.addons.connector_whs.tests.test_connector_wms import CommonConnectorWMS


@tagged("-standard", "test_wms")
class TestConnectorWmsWhs(CommonConnectorWMS):
    def setUp(self):
        super().setUp()
        dbsource_name = "Odoo WMS local server"
        dbsource = self.dbsource_model.search([("name", "=", dbsource_name)])
        if not dbsource:
            # connection string is something like:
            # mssql+pymssql://<user>:<password>@<ip>/<database>
            conn_file = os.path.join(os.path.expanduser("~"), "connection_wms_whs.txt")
            if not os.path.isfile(conn_file):
                raise UserError(_("Missing connection string!"))
            with open(conn_file, "r") as file:
                conn_string = file.read().replace("\n", "")
            # Enable WMS on picking types of Your Company only
            dbsource = self.dbsource_model.create(
                {
                    "name": dbsource_name,
                    "conn_string_sandbox": conn_string,
                    "connector": "mssql",  # noqa
                    "location_id": self.env.ref(
                        "stock.stock_location_stock"  # noqa
                    ).id,
                    "stock_picking_type_ids": [
                        (
                            6,
                            0,
                            self.env["stock.picking.type"]
                            .search(
                                [
                                    (
                                        "warehouse_id.company_id",
                                        "=",
                                        self.env.user.company_id.id,
                                    ),
                                    ("code", "!=", "mrp_operation"),
                                ]
                            )
                            .ids,
                        )
                    ],
                }
            )
        self.dbsource = dbsource
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=clean_sql_text("DELETE FROM HOST_LISTE"),
            sqlparams=None,
            metadata=None,
        )
        self.categ_id = self.env.ref("product.product_category_3")
        self.assertNotEqual(self.categ_id.name, "CUSTOM")
        self.custom_categ_id = self.env["product.category"].search(
            [
                ("name", "=", "CUSTOM"),
            ]
        )
        if not self.custom_categ_id:
            self.custom_categ_id = self.env["product.category"].create(
                {
                    "name": "CUSTOM",
                }
            )
        # int: 10 = prelievo, 11 = (prelievo per) assemblaggio, 20 = deposito
        self.causali = {
            "out": "10",
            "out_manufacturing": "11",
            "in": "20",
        }

    def _select_whs_liste_rif(self, riferimento):
        return self.dbsource.execute_mssql(
            sqlquery=clean_sql_text(
                "SELECT Elaborato FROM HOST_LISTE WHERE Riferimento=:Riferimento"
            ),
            sqlparams=dict(Riferimento=riferimento),
            metadata=None,
        )

    def _select_whs_liste(self, wms_list, elaborato=False):
        query = (
            "SELECT Qta, QtaMovimentata, Priorita, Causale FROM HOST_LISTE "
            "WHERE NumLista=:NUM_LISTA AND NumRiga=:NUM_RIGA"
        )
        sql_params = dict(
            NUM_LISTA=wms_list.num_lista,
            NUM_RIGA=wms_list.riga,
        )
        if elaborato:
            query += " AND Elaborato=:ELABORATO"
            sql_params.update(ELABORATO=elaborato)
        return self.dbsource.execute_mssql(
            sqlquery=clean_sql_text(query), sqlparams=sql_params, metadata=None
        )

    def simulate_whs_cron(self, whs_lists_dict, elaborato=4):
        whs_lists = self.env["hyddemo.whs.liste"]
        for whs_list in whs_lists_dict:
            whs_lists |= whs_list
        for num_lista in set(whs_lists.mapped("num_lista")):
            current_whs_lists = whs_lists.filtered(lambda x: x.num_lista == num_lista)
            for whs_list in current_whs_lists:
                set_liste_elaborated_query = (
                    "UPDATE HOST_LISTE SET Elaborato=:Elaborato, "
                    "QtaMovimentata=:QtaMov WHERE "
                    "NumLista=:NumLista AND NumRiga=:NumRiga"
                )
                self.dbsource.with_context(no_return=True).execute_mssql(
                    sqlquery=clean_sql_text(set_liste_elaborated_query),
                    sqlparams=dict(
                        Elaborato=elaborato,
                        QtaMov=whs_lists_dict[whs_list],
                        NumLista=whs_list.num_lista,
                        NumRiga=whs_list.riga,
                    ),
                    metadata=None,
                )

    def simulate_whs_cron_inventory(self, product, quantity):
        # check if there is a row with this product and update it, otherwise create one
        res = self.dbsource.execute_mssql(
            sqlquery=clean_sql_text(
                "SELECT Articolo, Qta FROM HOST_GIACENZE WHERE Articolo=:Articolo"
            ),
            sqlparams=dict(
                Articolo=product.default_code,
            ),
            metadata=None,
        )
        if res and res[0] and len(res[0]) == 1:
            giacenze_query = (
                "UPDATE HOST_GIACENZE SET Qta=:Qta WHERE Articolo=:Articolo"
            )
        else:
            giacenze_query = (
                "INSERT INTO HOST_GIACENZE (Articolo, Qta) VALUES (:Articolo, :Qta)"
            )
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=clean_sql_text(giacenze_query),
            sqlparams=dict(
                Articolo=product.default_code,
                Qta=quantity,
            ),
            metadata=None,
        )
        sync_stock_form = Form(
            self.env["wizard.sync.stock.whs.mssql"].with_context(
                active_id=self.dbsource.id,
                active_ids=self.dbsource.ids,
            )
        )
        sync_stock_form.do_sync = True
        sync_stock_form.product_id = product
        sync_stock = sync_stock_form.save()
        sync_stock.apply()

    def _check_cancel_workflow(self, picking, list_len):
        """
        This method is used to check the re-use of the same whs list linked to the
        picking when this is cancelled, without re-creating a new one.
        """
        riferimento = (
            picking.sale_id.name if picking.sale_id else picking.purchase_id.name
        )
        whs_records = self._select_whs_liste_rif(riferimento)[0]
        whs_lists = picking.mapped("move_lines.whs_list_ids")
        self.assertEqual(len(whs_lists), list_len)
        self.assertEqual(set(whs_lists.mapped("stato")), {"2"})
        picking.action_assign()
        if all(x.state == "assigned" for x in picking.move_lines):
            self.assertEqual(picking.state, "assigned")
        else:
            self.assertEqual(picking.state, "confirmed")
        picking.action_cancel()
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(picking.state, "cancel")
        # check whs lists are in stato '3' -> 'Da NON elaborare'
        self.assertEqual(set(picking.move_lines.mapped("whs_list_ids.stato")), {"3"})
        self.simulate_whs_cron(
            {x: x.qta for x in picking.move_lines.mapped("whs_list_ids")}, 5
        )
        riferimento = (
            picking.sale_id.name if picking.sale_id else picking.purchase_id.name
        )
        whs_records1 = self._select_whs_liste_rif(riferimento)[0]
        self.assertEqual(len(whs_records1), len(whs_records))
        self.assertEqual({x[0] for x in whs_records1}, {5})
        # restore picking to assigned state
        picking.action_back_to_draft()
        picking.action_confirm()
        if picking.sale_id:
            picking.action_assign()
        valid_whs_lists = picking.mapped("move_lines.whs_list_ids").filtered(
            lambda x: x.stato != "3"
        )
        self.assertEqual(len(valid_whs_lists), list_len)
        # check valid whs lists are added to the invalidated ones
        self.dbsource.whs_insert_read_and_synchronize_list()
        riferimento = (
            picking.sale_id.name if picking.sale_id else picking.purchase_id.name
        )
        whs_records2 = self._select_whs_liste_rif(riferimento)[0]
        # 4 whs lists of which 2 valid (stato=1) and 2 invalid (stato=3)
        self.assertEqual(len(whs_records2), len(whs_records) + list_len)
        for Elaborato in {x[0] for x in whs_records2}:
            # WHS cron change Elaborato to 2 in an un-controllable time
            self.assertIn(Elaborato, {5, 1, 2})
        return valid_whs_lists

    def _execute_select_all_valid_host_liste(self):
        # insert lists in WHS: this has to be invoked before every sql call!
        self.dbsource.whs_insert_read_and_synchronize_list()
        res = self.dbsource.execute_mssql(
            sqlquery=clean_sql_text("SELECT * FROM HOST_LISTE WHERE Qta!=:Qta"),
            sqlparams=dict(Qta=0),
            metadata=None,
        )
        return res and res[0] or []

    def test_00_complete_picking_from_sale(self):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()
        whs_len_records = len(self._execute_select_all_valid_host_liste())
        order_form1 = Form(self.env["sale.order"])
        order_form1.partner_id = self.partner
        order_form1.client_order_ref = "Rif. SO customer"
        with order_form1.order_line.new() as order_line:
            order_line.product_id = self.product1
            order_line.product_uom_qty = 5
            order_line.price_unit = 100
        with order_form1.order_line.new() as order_line:
            order_line.product_id = self.product_excluded
            order_line.product_uom_qty = 5
            order_line.price_unit = 100
        order1 = order_form1.save()
        order1.action_confirm()
        self.assertEqual(order1.state, "sale")
        picking1 = order1.picking_ids[0]
        self.assertEqual(len(picking1.mapped("move_lines.whs_list_ids")), 1)
        if all(x.state == "assigned" for x in picking1.move_lines):
            self.assertEqual(picking1.state, "assigned")
        else:
            self.assertEqual(picking1.state, "waiting")
        # check WMS list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self._execute_select_all_valid_host_liste()
        self.assertEqual(len(whs_records), whs_len_records + 1)
        for whs_record in whs_records:
            client_order_ref = whs_record[11]
            default_code = whs_record[17]
            product_code = whs_record[29]
            self.assertEqual(client_order_ref, order1.client_order_ref)
            if self.product1.default_code == default_code:
                self.assertEqual(
                    self.product1.customer_ids[0].product_code, product_code
                )
            else:
                self.assertEqual(  # FIXME era notEqual
                    self.product1.customer_ids[0].product_code, product_code
                )
        # check cancel workflow
        whs_lists = picking1.mapped("move_lines.whs_list_ids")
        self.assertEqual(len(whs_lists), 1)
        self.assertEqual(whs_lists.stato, "2")
        if all(x.state == "assigned" for x in picking1.move_lines):
            self.assertEqual(picking1.state, "assigned")
        else:
            self.assertEqual(picking1.state, "waiting")
        picking1.action_cancel()
        self.assertEqual(picking1.state, "cancel")
        # check WMS lists are in stato '3' -> 'Da NON elaborare'
        self.assertEqual(picking1.move_lines.mapped("whs_list_ids.stato"), ["3"])
        # restore picking to assigned state
        picking1.action_back_to_draft()
        picking1.action_confirm()
        picking1.action_assign()
        whs_lists = picking1.mapped("move_lines.whs_list_ids").filtered(
            lambda x: x.stato != "3"
        )
        self.assertEqual(len(whs_lists), 1)
        whs_list = whs_lists[0]
        self.assertTrue(whs_list)
        # check WMS list is added, and only 1 valid WMS list exists
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self._execute_select_all_valid_host_liste()
        self.assertEqual(len(whs_records), whs_len_records + 1)
        # simulate whs work
        lotto = "55A1"
        lotto2 = "55A2"
        lotto3 = "55A3"
        lotto4 = "55A4"
        lotto5 = "55A5"
        set_liste_elaborated_query = (
            "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=:QtaMov, "
            "Lotto=:Lotto, Lotto2=:Lotto2, Lotto3=:Lotto3, Lotto4=:Lotto4, "
            "Lotto5=:Lotto5 WHERE "
            "NumLista=:NumLista AND NumRiga=:NumRiga"
        )
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=clean_sql_text(set_liste_elaborated_query),
            sqlparams=dict(
                Lotto=lotto,
                Lotto2=lotto2,
                Lotto3=lotto3,
                Lotto4=lotto4,
                Lotto5=lotto5,
                QtaMov=whs_list.qta,
                NumLista=whs_list.num_lista,
                NumRiga=whs_list.riga,
            ),
            metadata=None,
        )

        whs_select_query = (
            "SELECT Qta, QtaMovimentata, Lotto, Lotto3, Lotto3, Lotto4, Lotto5 "
            "FROM HOST_LISTE WHERE Elaborato = 4 AND "
            "NumLista=:NumLista AND NumRiga=:NumRiga"
        )
        result_liste = self.dbsource.execute_mssql(
            sqlquery=clean_sql_text(whs_select_query),
            sqlparams=dict(
                NumLista=whs_list.num_lista,
                NumRiga=whs_list.riga,
            ),
            metadata=None,
        )
        self.assertEqual(
            str(result_liste[0]),
            "[(Decimal('5.000'), Decimal('5.000'), '55A1', '55A3', '55A3', '55A4', "
            "'55A5')]",
        )

        self.dbsource.whs_insert_read_and_synchronize_list()

        # check move and picking linked to sale order have changed state to done
        self.assertEqual(
            picking1.move_lines.filtered(
                lambda x: not x.product_id.exclude_from_whs
            ).state,
            "assigned",
        )
        self.assertEqual(picking1.state, "assigned")
        # check lot info
        self.assertEqual(whs_list.lotto, lotto)
        self.assertEqual(whs_list.lotto2, lotto2)
        self.assertEqual(whs_list.lotto3, lotto3)
        self.assertEqual(whs_list.lotto4, lotto4)
        self.assertEqual(whs_list.lotto5, lotto5)

    def test_01_partial_picking_from_sale(self):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()

        whs_len_records = len(self._execute_select_all_valid_host_liste())
        order_form1 = Form(self.env["sale.order"])
        order_form1.partner_id = self.partner
        order_form1.client_order_ref = "Rif. SO customer 1"
        with order_form1.order_line.new() as order_line:
            order_line.product_id = self.product1
            order_line.product_uom_qty = 5
            order_line.price_unit = 100
            order_line.priority = "1"
        with order_form1.order_line.new() as order_line:
            order_line.product_id = self.product1
            order_line.product_uom_qty = 5
            order_line.price_unit = 100
        order1 = order_form1.save()
        order1.action_confirm()
        self.assertEqual(order1.state, "sale")
        self.assertEqual(order1.priority, "1")
        self.assertEqual(order1.picking_ids.state, "assigned")
        picking = order1.picking_ids[0]
        self.assertEqual(len(picking.mapped("move_lines.whs_list_ids")), 2)
        self.assertEqual(
            len(set(picking.mapped("move_lines.whs_list_ids.num_lista"))), 1
        )

        # check WMS list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self.dbsource.execute_mssql(
            sqlquery=clean_sql_text(
                "SELECT Elaborato, NumLista, NumRiga, * FROM HOST_LISTE WHERE "
                "Qta!=:Qta"
            ),
            sqlparams=dict(Qta=0),
            metadata=None,
        )[0]
        self.assertEqual(len(whs_records), whs_len_records + 2)
        self.assertEqual({x[0] for x in whs_records}, {1})
        self.assertEqual(
            {x.stato for x in picking.mapped("move_lines.whs_list_ids")}, {"2"}
        )
        for whs_record in whs_records:
            client_order_ref = whs_record[11 + 3]
            default_code = whs_record[17 + 3]
            product_code = whs_record[29 + 3]
            self.assertEqual(client_order_ref, order1.client_order_ref)
            if self.product1.default_code == default_code:
                self.assertEqual(
                    self.product1.customer_ids[0].product_code, product_code
                )
            else:
                self.assertNotEqual(
                    self.product1.customer_ids[0].product_code, product_code
                )

        whs_lists = self._check_cancel_workflow(picking, 2)
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self.dbsource.execute_mssql(
            sqlquery=clean_sql_text(
                "SELECT Elaborato, NumLista, NumRiga FROM HOST_LISTE WHERE Qta!=:Qta"
            ),
            sqlparams=dict(Qta=0),
            metadata=None,
        )[0]
        self.assertEqual(len(whs_records), whs_len_records + 2)
        # simulate WMS work: validate first move partially (3 over 5)
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.simulate_whs_cron({x: 3 for x in whs_lists})
        # do not launch self.dbsource.whs_insert_read_and_synchronize_list() here as it
        # would change Elaborato from 4 to 5, as it must do
        for whs_list in whs_lists:
            result_liste = self._select_whs_liste(whs_list, 4)
            self.assertIn(
                f"[(Decimal('5.000'), Decimal('3.000'), 1, '{self.causali['out']}')]",
                str(result_liste),
            )

        self.dbsource.whs_insert_read_and_synchronize_list()

        # check move and picking linked to sale order have changed state to done
        self.assertEqual(set(picking.move_lines.mapped("state")), {"assigned"})
        if all(x.state == "assigned" for x in picking.move_lines):
            self.assertEqual(picking.state, "assigned")
        else:
            self.assertEqual(picking.state, "waiting")
        for move in picking.move_lines:
            # stock.move.line could be splitted, so check only stock.move
            self.assertAlmostEqual(move.quantity_done, 3.0)
        self.assertEqual(picking.state, "assigned")

        # simulate user partial validate of picking and check backorder exist
        res = picking.button_validate()
        Form(self.env[res["res_model"]].with_context(res["context"])).save().process()
        backorder_picking = order1.picking_ids - picking
        # Simulate WMS user validation
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_lists = backorder_picking.mapped("move_lines.whs_list_ids").filtered(
            lambda x: x.stato != "3"
        )
        for whs_list in whs_lists:
            # simulate whs work: total process
            set_liste_elaborated_query = (
                "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=:QtaMov WHERE "
                "NumLista=:NumLista AND NumRiga=:NumRiga"
            )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=clean_sql_text(set_liste_elaborated_query),
                sqlparams=dict(
                    QtaMov=whs_list.qta,
                    NumLista=whs_list.num_lista,
                    NumRiga=whs_list.riga,
                ),
                metadata=None,
            )

        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            whs_len_records + 4,
        )

        # check backorder picking is waiting for whs process
        self.assertEqual(len(order1.picking_ids), 2)
        self.assertEqual(backorder_picking.state, "assigned")
        self.assertEqual(backorder_picking.move_lines[0].state, "assigned")

    def test_02_partial_picking_partial_available_from_sale(self):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()
        whs_len_records = len(self._execute_select_all_valid_host_liste())
        order_form1 = Form(self.env["sale.order"])
        order_form1.partner_id = self.partner
        order_form1.client_order_ref = "Rif. SO customer 2"
        with order_form1.order_line.new() as order_line:
            order_line.product_id = self.product1
            order_line.product_uom_qty = 5
            order_line.priority = "2"
            order_line.price_unit = 100
        with order_form1.order_line.new() as order_line:
            order_line.product_id = self.product2
            order_line.product_uom_qty = 20
            order_line.price_unit = 100
        order1 = order_form1.save()
        order1.action_confirm()
        self.assertEqual(order1.state, "sale")
        self.assertEqual(order1.priority, "2")
        self.assertEqual(len(order1.picking_ids), 1)
        picking = order1.picking_ids
        self.assertEqual(picking.priority, "2")
        self.assertEqual(len(picking.mapped("move_lines.whs_list_ids")), 2)
        self.assertEqual(picking.state, "assigned")

        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self.dbsource.execute_mssql(
            sqlquery=clean_sql_text(
                "SELECT * FROM HOST_LISTE WHERE Elaborato!=:Elaborato AND Qta!=:Qta"
            ),
            sqlparams=dict(Elaborato=5, Qta=0),
            metadata=None,
        )[0]
        self.assertEqual(len(whs_records), whs_len_records + 2)
        for whs_record in whs_records:
            client_order_ref = whs_record[11]
            default_code = whs_record[17]
            product_code = whs_record[29]
            self.assertEqual(client_order_ref, order1.client_order_ref)
            if self.product1.default_code == default_code:
                self.assertEqual(
                    self.product1.customer_ids[0].product_code, product_code
                )
            else:
                self.assertNotEqual(
                    self.product1.customer_ids[0].product_code, product_code
                )

        # check backorder is not created without WMS list validation
        res = picking.button_validate()
        Form(self.env[res["res_model"]].with_context(res["context"])).save().process()
        # User cannot create backorder if WMS list is not processed on WMS system
        # TODO: check backorder is created for residual
        self.assertNotEqual(picking.state, "done")
        self.assertEqual(len(order1.picking_ids), 1)

        whs_lists = picking.mapped("move_lines.whs_list_ids")
        for whs_list in whs_lists:
            # simulate WMS work: partial processing (3 of 5) of product #1
            # and total (20 of 20) of product #2 so it is -4 on warehouse
            set_liste_elaborated_query = (
                "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=:QtaMov WHERE "
                "NumLista=:NumLista AND NumRiga=:NumRiga"
            )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=clean_sql_text(set_liste_elaborated_query),
                sqlparams=dict(
                    QtaMov=3 if whs_list.product_id == self.product1 else 20,
                    NumLista=whs_list.num_lista,
                    NumRiga=whs_list.riga,
                ),
                metadata=None,
            )
        # check WMS work is done correctly
        for whs_list in whs_lists:
            result_liste = self._select_whs_liste(whs_list, 4)
            self.assertEqual(
                str(result_liste[0]),
                f"[(Decimal('5.000'), Decimal('3.000'), 2, '{self.causali['out']}')]"
                if whs_list.product_id == self.product1
                else f"[(Decimal('20.000'), Decimal('20.000'), 2, '{self.causali['out']}')]",
            )

        self.dbsource.whs_insert_read_and_synchronize_list()

        # check move and picking linked to sale order have changed state to done
        for move in picking.move_lines:
            # stock.move.line could be splitted, so check only stock.move
            self.assertAlmostEqual(
                move.quantity_done, 3.0 if move.product_id == self.product1 else 20
            )
        picking.action_assign()
        self.assertEqual(picking.state, "assigned")
        # check that action_assign run by scheduler do not change state
        self.run_stock_procurement_scheduler()
        picking.action_assign()
        self.assertEqual(picking.state, "assigned")

        # simulate user partial validate of picking and check backorder exist
        res = picking.button_validate()
        backorder_wiz = Form(
            self.env[res["res_model"]].with_context(res["context"])
        ).save()
        # User cannot create backorder if WMS list is not processed on WMS system
        # with self.assertRaises(UserError):
        # TODO: check backorder is created for residual
        backorder_wiz.process()

        # Simulate WMS user validation
        whs_lists = picking.mapped("move_lines.whs_list_ids")
        for whs_list in whs_lists:
            # simulate whs work: total process
            set_liste_elaborated_query = (
                "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=:QtaMov WHERE "
                "NumLista=:NumLista AND NumRiga=:NumRiga"
            )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=clean_sql_text(set_liste_elaborated_query),
                sqlparams=dict(
                    QtaMov=2 if whs_list.product_id == self.product2 else 3,
                    NumLista=whs_list.num_lista,
                    NumRiga=whs_list.riga,
                ),
                metadata=None,
            )

        # this function do the action_assign() too
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(picking.state, "done")

        # check back picking is waiting as Odoo qty is not considered
        self.assertEqual(len(order1.picking_ids), 2)
        backorder_picking = order1.picking_ids - picking
        back_whs_list = backorder_picking.mapped("move_lines.whs_list_ids")
        self.assertEqual(backorder_picking.move_lines.mapped("state"), ["assigned"])
        # todo check also a 'partially_available'
        self.assertEqual(backorder_picking.state, "assigned")

        # todo check whs_list for backorder is created
        self.dbsource.whs_insert_read_and_synchronize_list()
        result_liste = self._select_whs_liste(back_whs_list)
        self.assertEqual(
            str(result_liste[0]),
            f"[(Decimal('2.000'), None, 2, '{self.causali['out']}')]",
        )

        # simulate whs work set done to rest of backorder
        self.simulate_whs_cron({x: 2 for x in back_whs_list})

        self.dbsource.whs_insert_read_and_synchronize_list()
        backorder_picking.button_validate()
        self.assertEqual(backorder_picking.state, "done")

    def test_03_partial_picking_from_sale(self):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()
        whs_len_records = len(self._execute_select_all_valid_host_liste())
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
            order_line.priority = "0"
        with order_form1.order_line.new() as order_line:
            order_line.product_id = self.product4
            order_line.product_uom_qty = 20  # 0
            order_line.price_unit = 100
        order1 = order_form1.save()
        order1.action_confirm()
        self.assertEqual(order1.state, "sale")
        self.assertEqual(order1.mapped("picking_ids.state"), ["assigned"])
        picking = order1.picking_ids[0]
        self.assertEqual(len(picking.mapped("move_lines.whs_list_ids")), 4)

        # check WMS list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self._execute_select_all_valid_host_liste()
        self.assertEqual(len(whs_records), whs_len_records + 4)
        for whs_record in whs_records:
            client_order_ref = whs_record[11]
            default_code = whs_record[17]
            product_code = whs_record[29]
            self.assertEqual(client_order_ref, order1.client_order_ref)
            if self.product1.default_code == default_code:
                self.assertEqual(
                    self.product1.customer_ids[0].product_code, product_code
                )
            else:
                self.assertNotEqual(
                    self.product1.customer_ids[0].product_code, product_code
                )
        # simulate WMS work: validate first move totally and second move partially
        whs_lists = picking.mapped("move_lines.whs_list_ids")
        self.simulate_whs_cron(
            {x: 0 if x.product_id == self.product3 else 5 for x in whs_lists}
        )

        for whs_l in whs_lists:
            result_liste = self._select_whs_liste(whs_l, 4)
            self.assertEqual(
                str(result_liste[0]),
                f"[(Decimal('5.000'), Decimal('5.000'), 0, '{self.causali['out']}')]"
                if whs_l.product_id == self.product1
                else f"[(Decimal('10.000'), Decimal('5.000'), 0, '{self.causali['out']}')]"
                if whs_l.product_id == self.product2
                else f"[(Decimal('20.000'), Decimal('0.000'), 0, '{self.causali['out']}')]"
                if whs_l.product_id == self.product3
                else f"[(Decimal('20.000'), Decimal('5.000'), 0, '{self.causali['out']}')]",
            )

        self.dbsource.whs_insert_read_and_synchronize_list()

        # check move and picking linked to sale order have changed state to done
        for move_line in picking.move_lines:
            for stock_move_line in move_line.move_line_ids:
                if stock_move_line.product_id in [
                    self.product1,
                    self.product2,
                    self.product4,
                ]:
                    self.assertAlmostEqual(stock_move_line.qty_done, 5.0)
                if stock_move_line.product_id == self.product3:
                    self.assertAlmostEqual(stock_move_line.qty_done, 0)
        self.run_stock_procurement_scheduler()
        # check that action_assign run by scheduler do not change state
        # self.assertEqual(picking.state, "confirmed")
        picking.action_assign()
        self.assertEqual(picking.state, "assigned")

        # simulate user partial validate of picking and check backorder exist
        res = picking.button_validate()
        backorder_wiz = Form(
            self.env[res["res_model"]].with_context(res["context"])
        ).save()
        # User must set correctly quantity as set by WHS user, ignoring qty set
        # different by Odoo or a user, so set a qty different and check that error is
        # raised without intervent
        for move_line in picking.move_lines:
            if move_line.product_id == self.product1:
                move_line.quantity_done = 0
        with self.assertRaises(UserError):
            backorder_wiz.process()
        for move_line in picking.move_lines:
            move_line.quantity_done = (
                5
                if move_line.product_id in [self.product1, self.product2, self.product4]
                else 0
            )
        backorder_wiz.process()
        self.assertEqual(picking.state, "done")
        # check backorder WMS list has the correct qty
        self.assertEqual(len(order1.picking_ids), 2)
        backorder_picking = order1.picking_ids - picking
        for move_line in backorder_picking.move_lines:
            self.assertAlmostEqual(
                move_line.whs_list_ids[0].qta,
                5
                if move_line.product_id == self.product2
                else 20
                if move_line.product_id == self.product3
                else 15,
            )

        # Simulate WMS user validation
        whs_lists = picking.mapped("move_lines.whs_list_ids")
        self.simulate_whs_cron({x: x.qta for x in whs_lists})
        self.dbsource.whs_insert_read_and_synchronize_list()
        # check WMS list for backorder is not created as the first is completed entirely
        # FIXME: what does the note above mean?
        res = self._execute_select_all_valid_host_liste()
        self.assertEqual(len(res), whs_len_records + 6)
        # self.run_stock_procurement_scheduler()
        backorder_picking.action_assign()

    def test_04_unlink_sale_order(self):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()
        whs_len_records = len(self._execute_select_all_valid_host_liste())
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
        self.assertEqual(len(picking.mapped("move_lines.whs_list_ids")), 2)

        # check WMS list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            whs_len_records + 2,
        )
        # controlla che le liste WMS siano annullate (impostate con Qta=0)
        order1.action_cancel()
        # insert lists in WMS: this has to be invoked before every sql call!
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            whs_len_records,
        )
        self.assertEqual(
            set(order1.mapped("picking_ids.move_lines.whs_list_ids.stato")), {"3"}
        )
        order1.action_draft()
        order1.action_confirm()
        picking = order1.picking_ids.filtered(lambda x: x.state != "cancel")
        self.assertEqual(picking.mapped("move_lines.whs_list_ids.stato"), ["1", "1"])
        # insert lists in WMS: this has to be invoked before every sql call!
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            whs_len_records + 2,
        )
        # self.run_stock_procurement_scheduler()
        picking.action_assign()
        self.assertEqual(picking.state, "assigned")
        hyddemo_whs_lists = picking.mapped("move_lines.whs_list_ids")
        lists = {x.riga: x.num_lista for x in hyddemo_whs_lists}
        # simulate launch from WMS user
        set_liste_elaborating_query = (
            "UPDATE HOST_LISTE SET Elaborato=3 WHERE "
            " %s "
            % (
                " OR ".join(
                    "(NumLista = '%s' AND NumRiga = '%s')" % (lists[y], y)
                    for y in lists
                )
            )
        )
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=clean_sql_text(set_liste_elaborating_query),
            sqlparams=None,
            metadata=None,
        )
        with self.assertRaises(UserError):
            order1.action_cancel()
        # Check product added to sale order after confirmation create new WMS lists
        # adding product to an existing open picking
        whs_len_records = len(self._execute_select_all_valid_host_liste())
        order_form2 = Form(order1)
        with order_form2.order_line.new() as order_line:
            order_line.product_id = self.product4
            order_line.product_uom_qty = 5
            order_line.price_unit = 100
        order1 = order_form2.save()
        pickings = order1.picking_ids.filtered(lambda x: x.state == "assigned")
        pickings.action_assign()
        new_product_move_line_ids = order1.picking_ids.mapped("move_lines").filtered(
            lambda x: x.product_id == self.product4
        )
        self.assertTrue(new_product_move_line_ids.mapped("whs_list_ids"))
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            whs_len_records + 1,
        )

        # test change qty of sale order line is forbidden
        with self.assertRaises(UserError):
            order1.order_line[0].write({"product_uom_qty": 17})

    def test_06_purchase(self):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()
        self.simulate_whs_cron_inventory(self.product2, 8)
        whs_len_records = len(self._execute_select_all_valid_host_liste())
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
            purchase.state, "purchase", 'Purchase state should be "Purchase"'
        )
        move_line = purchase.picking_ids.move_lines.filtered(
            lambda x: x.product_id == self.product2
        )
        order_line = purchase.order_line.filtered(
            lambda x: x.product_id == self.product2
        )
        order_line.product_qty = 17
        # update directly as it is a readonly field in view and Form() doesn't work
        move_line.product_uom_qty = 17
        self.assertEqual(order_line.product_qty, move_line.whs_list_ids.qta)
        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            whs_len_records + 2,
        )
        # get available qty for product2 before purchase order
        qty_available_product2 = self.product2.qty_available
        # simulate WMS work: partial processing of product #2
        # and total of product #3
        whs_lists = purchase.mapped("picking_ids.move_lines.whs_list_ids")
        self.simulate_whs_cron(
            {x: 2 if x.product_id == self.product2 else 3 for x in whs_lists}
        )
        for whs_list in whs_lists:
            result_liste = self._select_whs_liste(whs_list, 4)
            self.assertEqual(
                str(result_liste[0]),
                f"[(Decimal('17.000'), Decimal('2.000'), 0, '{self.causali['in']}')]"
                if whs_list.product_id == self.product2
                else f"[(Decimal('3.000'), Decimal('3.000'), 0, '{self.causali['in']}')]",
            )

        # this update Odoo from WHS
        self.dbsource.whs_insert_read_and_synchronize_list()
        # check whs_list are elaborated
        for whs_list in whs_lists:
            result_liste = self._select_whs_liste(whs_list, 5)
            self.assertEqual(
                str(result_liste[0]),
                f"[(Decimal('17.000'), Decimal('2.000'), 0, '{self.causali['in']}')]"
                if whs_list.product_id == self.product2
                else f"[(Decimal('3.000'), Decimal('3.000'), 0, '{self.causali['in']}')]",
            )

        # sync inventory to test this product is not considered even if the user
        # hasn't completed the picking
        # WHSystem already has the 2 pc income from purchase order, so we add them
        self.simulate_whs_cron_inventory(self.product2, self.product2.qty_available + 2)
        new_qty_available_product2 = self.product2.qty_available
        self.assertAlmostEqual(qty_available_product2, new_qty_available_product2, 2)

        # simulate user partial validate of picking and check backorder exist
        picking = purchase.picking_ids[0]
        picking.action_assign()
        if all(x.state == "assigned" for x in picking.move_lines):
            self.assertEqual(picking.state, "assigned")
        else:
            self.assertEqual(picking.state, "waiting")
        # check that action_assign run by scheduler do not change state
        picking.action_assign()
        self.assertEqual(picking.state, "assigned")
        res = picking.button_validate()
        wiz = Form(self.env[res["res_model"]].with_context(res["context"])).save()
        wiz.process()
        self.assertEqual(picking.state, "done")

        # check back picking is waiting as waiting for WMS work
        self.assertEqual(len(purchase.picking_ids), 2)
        backorder_picking = purchase.picking_ids - picking
        # self.run_stock_procurement_scheduler()
        backorder_picking.action_assign()
        if all(x.state == "assigned" for x in backorder_picking.move_lines):
            self.assertEqual(backorder_picking.state, "assigned")

        # check whs_list for backorder is created
        self.dbsource.whs_insert_read_and_synchronize_list()
        back_whs_list = backorder_picking.mapped("move_lines.whs_list_ids")
        result_liste = self._select_whs_liste(back_whs_list)
        self.assertEqual(
            str(result_liste[0]),
            f"[(Decimal('15.000'), None, 0, '{self.causali['in']}')]",
        )
        # TODO check cancel workflow without action_assign that create WMS list anyway
        self._check_cancel_workflow(backorder_picking, 1)
        backorder_picking.action_assign()
        # simulate WMS work set done to rest of backorder
        self.simulate_whs_cron({x: 18 for x in back_whs_list}, 4)

        self.dbsource.whs_insert_read_and_synchronize_list()
        backorder_picking.button_validate()
        self.assertEqual(backorder_picking.state, "assigned")
        # self.run_stock_procurement_scheduler()
        backorder_picking.action_assign()
        self.assertEqual(backorder_picking.state, "assigned")
        self.assertFalse(
            all(
                whs_list.stato == "3"
                for whs_list in backorder_picking.move_lines.whs_list_ids
            )
        )
        # Check product added to purchase order after confirm create WMS list with
        # different date_planned which create a new picking (as this module depends on
        # purchase_delivery_split_date)
        whs_len_records = len(self._execute_select_all_valid_host_liste())
        purchase_form = Form(purchase)
        with purchase_form.order_line.new() as po_line:
            po_line.product_id = self.product4
            po_line.product_qty = 20
            po_line.product_uom = self.product4.uom_po_id
            po_line.name = self.product4.name
            po_line.price_unit = 100
            po_line.date_planned = fields.Datetime.today() + relativedelta(month=2)
        purchase_form.save()
        # new_picking = purchase.picking_ids - (picking | backorder_picking)
        # new_picking.action_assign()
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            whs_len_records + 1,
        )
        # Check product added to purchase order after confirmation create new WMS lists
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
        new_product_move_line_ids = purchase.picking_ids.mapped("move_lines").filtered(
            lambda x: x.product_id == self.product5
        )
        self.assertTrue(new_product_move_line_ids.mapped("whs_list_ids"))
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            whs_len_records + 3,
        )

        # test qty change on purchase order line, which create a new line with increased
        # qty on picking
        po_line_to_change = purchase.order_line.filtered(
            lambda x: x.product_id == self.product5
        )[-1]
        po_line_to_change.write({"product_qty": 27})
        pickings = purchase.picking_ids.filtered(lambda x: x.state == "assigned")
        pickings.action_assign()
        po_whs_list = po_line_to_change.mapped("move_ids.whs_list_ids").filtered(
            lambda x: x.qta == 7
        )
        self.dbsource.whs_insert_read_and_synchronize_list()
        result_liste = self._select_whs_liste(po_whs_list)
        # WMS list is created for the increased qty
        self.assertEqual(
            str(result_liste[0]),
            f"[(Decimal('7.000'), None, 0, '{self.causali['in']}')]")

        # TODO test user can receive in WHS a qty > move quantity

    def test_07_1_purchase_no_backorder_with_less_qty(self):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()
        whs_len_records = len(self._execute_select_all_valid_host_liste())
        purchase_form = Form(self.env["purchase.order"])
        purchase_form.partner_id = self.partner
        with purchase_form.order_line.new() as po_line:
            po_line.product_id = self.product2
            po_line.product_qty = 20
            po_line.product_uom = self.product2.uom_po_id
            po_line.name = self.product2.name
            po_line.price_unit = 100
            po_line.date_planned = fields.Datetime.today() + relativedelta(month=1)
        purchase = purchase_form.save()
        purchase.button_approve()
        self.assertEqual(
            purchase.state, "purchase", 'Purchase state should be "Purchase"'
        )
        order_line = purchase.order_line
        move_line = purchase.picking_ids.move_lines
        self.assertEqual(order_line.product_qty, move_line.whs_list_ids.qta)
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            whs_len_records + 1,
        )
        # simulate whs work: partial processing of product #2
        whs_list = purchase.mapped("picking_ids.move_lines.whs_list_ids")
        self.simulate_whs_cron({x: 7 for x in whs_list})
        result_liste = self._select_whs_liste(whs_list, elaborato=4)
        self.assertEqual(
            str(result_liste[0]),
            f"[(Decimal('20.000'), Decimal('7.000'), 0, '{self.causali['in']}')]",
        )
        # this update Odoo from WHS
        self.dbsource.whs_insert_read_and_synchronize_list()
        # check whs_list are elaborated
        result_liste = self._select_whs_liste(whs_list, 5)
        self.assertEqual(
            str(result_liste[0]),
            f"[(Decimal('20.000'), Decimal('7.000'), 0, '{self.causali['in']}')]",
        )

        # simulate user partial validate of picking and check backorder does not exist
        picking = purchase.picking_ids
        picking.action_assign()
        if all(x.state == "assigned" for x in picking.move_lines):
            self.assertEqual(picking.state, "assigned")
        else:
            self.assertEqual(picking.state, "waiting")
        res = picking.button_validate()
        picking_form = Form(self.env[res["res_model"]].with_context(res["context"]))
        picking_form.save().process_cancel_backorder()
        self.assertEqual(picking.state, "done")
        whs_lists = purchase.mapped("picking_ids.move_lines.whs_list_ids")
        self.assertEqual(len(whs_lists), 2)
        whs_lists = self.env["hyddemo.whs.liste"].search(
            [("riferimento", "=", purchase.name)]
        )
        self.assertEqual(len(whs_lists), 2)  # fixme era 1

    def test_07_2_purchase_with_more_qty(self):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()
        whs_len_records = len(self._execute_select_all_valid_host_liste())
        purchase_form = Form(self.env["purchase.order"])
        purchase_form.partner_id = self.partner
        with purchase_form.order_line.new() as po_line:
            po_line.product_id = self.product2
            po_line.product_qty = 20
            po_line.product_uom = self.product2.uom_po_id
            po_line.name = self.product2.name
            po_line.price_unit = 100
            po_line.date_planned = fields.Datetime.today() + relativedelta(month=1)
        purchase = purchase_form.save()
        purchase.button_approve()
        self.assertEqual(
            purchase.state, "purchase", 'Purchase state should be "Purchase"'
        )
        order_line = purchase.order_line
        move_line = purchase.picking_ids.move_lines
        self.assertEqual(order_line.product_qty, move_line.whs_list_ids.qta)
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            whs_len_records + 1,
        )
        # simulate whs work: processing more qty than requested for product #2
        whs_list = purchase.mapped("picking_ids.move_lines.whs_list_ids")
        self.simulate_whs_cron({x: 27 for x in whs_list})
        result_liste = self._select_whs_liste(whs_list, 4)
        self.assertEqual(
            str(result_liste[0]),
            f"[(Decimal('20.000'), Decimal('27.000'), 0, '{self.causali['in']}')]",
        )
        # this update Odoo from WHS
        self.dbsource.whs_insert_read_and_synchronize_list()
        # check whs_list are elaborated
        result_liste = self._select_whs_liste(whs_list, 5)
        self.assertEqual(
            str(result_liste[0]),
            f"[(Decimal('20.000'), Decimal('27.000'), 0, '{self.causali['in']}')]",
        )

        # simulate user partial validate of picking and check backorder does not exist
        picking = purchase.picking_ids
        picking.action_assign()
        if all(x.state == "assigned" for x in picking.move_lines):
            self.assertEqual(picking.state, "assigned")
        else:
            self.assertEqual(picking.state, "waiting")
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        whs_lists = purchase.mapped("picking_ids.move_lines.whs_list_ids")
        self.assertEqual(len(whs_lists), 1)
        whs_lists = self.env["hyddemo.whs.liste"].search(
            [("riferimento", "=", purchase.name)]
        )
        self.assertEqual(len(whs_lists), 1)

    def _mrp_partial_from_sale(self, is_custom=False):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()
        whs_len_records = len(self._execute_select_all_valid_host_liste())
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.env.ref("base.res_partner_12")
        order_form.date_order = fields.Date.today()
        order_form.picking_policy = "direct"
        with order_form.order_line.new() as line:
            line.product_id = self.top_product
            line.product_uom_qty = 20
            line.product_uom = self.top_product.uom_po_id
            line.price_unit = self.top_product.list_price
            line.name = self.top_product.name
        order = order_form.save()
        order.action_confirm()
        self.assertEqual(order.state, "sale")
        man_order = self.env["mrp.production"].search([("origin", "ilike", order.name)])
        self.assertTrue(man_order)
        man_order.action_confirm()
        self.assertEqual(man_order.state, "confirmed")
        man_order.qty_producing = 5
        self._auto_fill_consumed_qty(man_order.move_raw_ids)
        self.assertTrue(man_order.move_raw_ids.move_line_ids)
        # self.assertTrue(man_order.move_finished_ids.move_line_ids)
        # self.assertEqual(
        #     man_order.move_finished_ids.move_line_ids.mapped("state"), ["confirmed"]
        # )
        man_order.button_send_to_whs()
        self.assertTrue(man_order.sent_to_whs)
        # check whs list are added: 3 components and 1 finished product
        self.dbsource.whs_insert_read_and_synchronize_list()
        created_whs_list_number = (
            3
            if self.warehouse.mto_pull_id.route_id in man_order.product_id.route_ids
            and is_custom
            else 4
        )
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            whs_len_records + created_whs_list_number,
        )

        # simulate whs work: consume 25% of components to produce 5 finished product
        # consumed and finished product are sent to WHS for the consumed/produced qty
        component_whs_lists = man_order.mapped("move_raw_ids.whs_list_ids")
        finished_whs_lists = man_order.mapped("move_finished_ids.whs_list_ids")
        self.simulate_whs_cron({x: x.qta * 0.25 for x in component_whs_lists})
        self.simulate_whs_cron({x: 5 for x in finished_whs_lists})

        for whs_list in component_whs_lists | finished_whs_lists:
            result_liste = self._select_whs_liste(whs_list, 4)
            causale = (
                self.causali["out_manufacturing"] if is_custom else self.causali["out"]
            )
            if whs_list.product_id == self.subproduct_1_1:
                self.assertEqual(whs_list.tipo, "5" if is_custom else "1")
                self.assertIn(
                    str(result_liste[0]),
                    [
                        f"[(Decimal('200.000'), Decimal('50.000'), 0, '{causale}')]",
                        f"[(Decimal('120.000'), Decimal('30.000'), 0, '{causale}')]",
                    ],
                )
            elif whs_list.product_id == self.subproduct_2_1:
                self.assertEqual(whs_list.tipo, "5" if is_custom else "1")
                self.assertEqual(
                    str(result_liste[0]),
                    f"[(Decimal('160.000'), Decimal('40.000'), 0, '{causale}')]",
                )
            elif whs_list.product_id == self.top_product:
                self.assertEqual(
                    str(result_liste[0]),
                    f"[(Decimal('20.000'), Decimal('5.000'), 0, '{self.causali['in']}')]",
                )

        # this update Odoo from WHS
        self.dbsource.whs_insert_read_and_synchronize_list()
        action = man_order.with_context(test_connector_whs=True).button_mark_done()
        backorder_form = Form(
            self.env["mrp.production.backorder"].with_context(**action["context"])
        )
        backorder_form.save().action_backorder()
        self.assertEqual(len(man_order.procurement_group_id.mrp_production_ids), 2)
        self.assertEqual(man_order.state, "done")

        mo_backorder = man_order.procurement_group_id.mrp_production_ids[-1]
        self.assertEqual(mo_backorder.state, "confirmed")
        with self.assertRaises(UserError):
            # check production ore cannot be done without WHS lists
            mo_backorder.with_context(test_connector_whs=True).button_mark_done()

    def test_08_mrp_partial_from_sale(self):
        self.top_product.categ_id = self.categ_id
        self.assertNotEqual(self.top_product.categ_id.name, "CUSTOM")
        self._mrp_partial_from_sale()

    def test_08_mrp_partial_from_sale_custom(self):
        self.top_product.categ_id = self.custom_categ_id
        self.assertEqual(self.top_product.categ_id.name, "CUSTOM")
        self._mrp_partial_from_sale(is_custom=True)

    def _mrp_total_from_sale(self, is_custom=False):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()
        whs_len_records = len(self._execute_select_all_valid_host_liste())
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.env.ref("base.res_partner_12")
        order_form.date_order = fields.Date.today()
        order_form.picking_policy = "direct"
        with order_form.order_line.new() as line:
            line.product_id = self.top_product
            line.product_uom_qty = 20
            line.product_uom = self.top_product.uom_po_id
            line.price_unit = self.top_product.list_price
            line.name = self.top_product.name
        order = order_form.save()
        order.action_confirm()
        self.assertEqual(order.state, "sale")
        man_order = self.env["mrp.production"].search([("origin", "ilike", order.name)])
        self.assertTrue(man_order)
        man_order.action_confirm()
        self.assertEqual(man_order.state, "confirmed")
        man_order.qty_producing = 20
        self._auto_fill_consumed_qty(man_order.move_raw_ids)
        self.assertTrue(man_order.move_raw_ids.move_line_ids)
        # self.assertTrue(man_order.move_finished_ids.move_line_ids)
        # self.assertEqual(
        #     man_order.move_finished_ids.move_line_ids.mapped("state"), ["confirmed"]
        # )
        man_order.button_send_to_whs()
        self.assertTrue(man_order.sent_to_whs)
        # check whs list are added: 3 components and 1 finished product
        self.dbsource.whs_insert_read_and_synchronize_list()
        created_whs_list_number = (
            3
            if self.warehouse.mto_pull_id.route_id in man_order.product_id.route_ids
            and is_custom
            else 4
        )
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            whs_len_records + created_whs_list_number,
        )

        # simulate whs work: consume 25% of components to produce 5 finished product
        component_whs_lists = man_order.mapped("move_raw_ids.whs_list_ids")
        finished_whs_lists = man_order.mapped("move_finished_ids.whs_list_ids")
        self.simulate_whs_cron({x: x.qta * 0.25 for x in component_whs_lists})
        self.simulate_whs_cron({x: 5 for x in finished_whs_lists})

        for whs_list in component_whs_lists | finished_whs_lists:
            result_liste = self._select_whs_liste(whs_list, 4)
            causale = (
                self.causali["out_manufacturing"] if is_custom else self.causali["out"]
            )
            if whs_list.product_id == self.subproduct_1_1:
                self.assertEqual(whs_list.tipo, "5" if is_custom else "1")
                self.assertIn(
                    str(result_liste[0]),
                    [
                        f"[(Decimal('200.000'), Decimal('50.000'), 0, '{causale}')]",
                        f"[(Decimal('120.000'), Decimal('30.000'), 0, '{causale}')]",
                    ],
                )
            elif whs_list.product_id == self.subproduct_2_1:
                self.assertEqual(whs_list.tipo, "5" if is_custom else "1")
                self.assertEqual(
                    str(result_liste[0]),
                    f"[(Decimal('160.000'), Decimal('40.000'), 0, '{causale}')]",
                )
            elif whs_list.product_id == self.top_product:
                self.assertEqual(
                    str(result_liste[0]),
                    f"[(Decimal('20.000'), Decimal('5.000'), 0, '{self.causali['in']}')]",
                )

        # this update Odoo from WHS
        self.dbsource.whs_insert_read_and_synchronize_list()

        man_order.with_context(test_connector_whs=True).button_mark_done()
        self.assertEqual(len(man_order.procurement_group_id.mrp_production_ids), 1)
        self.assertEqual(man_order.state, "progress")

    def test_09_mrp_total_from_sale(self):
        self.top_product.categ_id = self.categ_id
        self.assertNotEqual(self.top_product.categ_id.name, "CUSTOM")
        self._mrp_total_from_sale()

    def test_09_mrp_total_from_sale_custom(self):
        self.top_product.categ_id = self.custom_categ_id
        self.assertEqual(self.top_product.categ_id.name, "CUSTOM")
        self._mrp_total_from_sale(is_custom=True)
