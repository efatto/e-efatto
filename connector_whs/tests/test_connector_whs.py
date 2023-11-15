# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import time

from sqlalchemy import text as sql_text

from odoo import _, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import Form, SingleTransactionCase
from odoo.tools import mute_logger, relativedelta


class TestConnectorWhs(SingleTransactionCase):
    def setUp(self):
        super().setUp()
        dbsource_model = self.env["base.external.dbsource"]
        dbsource = dbsource_model.search([("name", "=", "Odoo WHS local server")])
        if not dbsource:
            conn_file = os.path.join(os.path.expanduser("~"), "connection_string.txt")
            if not os.path.isfile(conn_file):
                raise UserError(_("Missing connection string!"))
            with open(conn_file, "r") as file:
                conn_string = file.read().replace("\n", "")
            dbsource = dbsource_model.create(
                {
                    "name": "Odoo WHS local server",
                    "conn_string_sandbox": conn_string,
                    "connector": "mssql",
                    "location_id": self.env.ref("stock.stock_location_stock").id,
                }
            )
        self.dbsource = dbsource
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=sql_text("DELETE FROM HOST_LISTE"), sqlparams=None, metadata=None
        )
        self.src_location = self.env.ref("stock.stock_location_stock")
        self.dest_location = self.env.ref("stock.stock_location_customers")
        self.manufacture_location = self.env["stock.location"].search(
            [("usage", "=", "production")], limit=1
        )[0]
        self.procurement_model = self.env["procurement.group"]
        self.partner = self.env.ref("base.res_partner_2")
        # Create product with 16 on hand
        self.product1 = self.env["product.product"].create(
            [
                {
                    "name": "test product1",
                    "default_code": "PRODUCT1",
                    "type": "product",
                }
            ]
        )
        self.StockQuant = self.env["stock.quant"]
        self.quant_product1 = self.StockQuant.create(
            [
                {
                    "product_id": self.product1.id,
                    "location_id": self.src_location.id,
                    "quantity": 16.0,
                }
            ]
        )
        # Create product with 8 on hand
        self.product2 = self.env["product.product"].create(
            [
                {
                    "name": "test product2",
                    "default_code": "PRODUCT2",
                    "type": "product",
                }
            ]
        )
        self.quant_product2 = self.StockQuant.create(
            [
                {
                    "product_id": self.product2.id,
                    "location_id": self.src_location.id,
                    "quantity": 8.0,
                }
            ]
        )
        # Large Cabinet, 250 on hand
        self.product3 = self.env.ref("product.product_product_6")
        # Drawer Black, 0 on hand
        self.product4 = self.env.ref("product.product_product_16")
        self.product5 = self.env.ref("product.product_product_20")
        self.product1.invoice_policy = "order"
        self.product1.write(
            {
                "customer_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.partner.id,
                            "product_code": "CUSTOMERCODE",
                            "product_name": "Product customer name",
                        },
                    )
                ]
            }
        )
        self.product2.invoice_policy = "order"

    def run_stock_procurement_scheduler(self):
        with mute_logger("odoo.addons.stock.models.procurement"):
            self.procurement_model.run_scheduler(True)
            time.sleep(30)

    def simulate_whs_cron(self, whs_lists, elaborato):
        for whs_list in whs_lists:
            set_liste_elaborated_query = (
                "UPDATE HOST_LISTE SET Elaborato=%s, QtaMovimentata=%s WHERE "
                "NumLista = '%s' AND NumRiga = '%s'"
                % (elaborato, whs_list.qta, whs_list.num_lista, whs_list.riga)
            )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(set_liste_elaborated_query),
                sqlparams=None,
                metadata=None,
            )

    def _check_cancel_workflow(self, picking, list_len):
        """
        This method is used to check the re-use of the same whs list linked to the
        picking when this is cancelled, without re-creating a new one.
        """
        whs_records = self.dbsource.execute_mssql(
            sqlquery=sql_text(
                "SELECT Elaborato, NumLista, NumRiga, * FROM HOST_LISTE "
                "WHERE Riferimento=:Riferimento"
            ),
            sqlparams=dict(
                Riferimento=picking.sale_id.name
                if picking.sale_id
                else picking.purchase_id.name
            ),
            metadata=None,
        )[0]
        whs_lists = picking.mapped("move_lines.whs_list_ids")
        self.assertEqual(len(whs_lists), list_len)
        self.assertEqual(set(whs_lists.mapped("stato")), {"2"})
        picking.action_assign()
        if all(x.state == "assigned" for x in picking.move_lines):
            self.assertEqual(picking.state, "assigned")
        else:
            self.assertEqual(picking.state, "confirmed")  # era waiting, non rilevante
        picking.action_cancel()
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(picking.state, "cancel")
        # check whs lists are in stato '3' -> 'Da NON elaborare'
        self.assertEqual(set(picking.move_lines.mapped("whs_list_ids.stato")), {"3"})
        self.simulate_whs_cron(picking.move_lines.mapped("whs_list_ids"), 5)
        whs_records1 = self.dbsource.execute_mssql(
            sqlquery=sql_text(
                "SELECT Elaborato, NumLista, NumRiga, * FROM HOST_LISTE "
                "WHERE Riferimento=:Riferimento"
            ),
            sqlparams=dict(
                Riferimento=picking.sale_id.name
                if picking.sale_id
                else picking.purchase_id.name
            ),
            metadata=None,
        )[0]
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
        whs_records2 = self.dbsource.execute_mssql(
            sqlquery=sql_text(
                "SELECT Elaborato, NumLista, NumRiga, * FROM HOST_LISTE "
                "WHERE Riferimento=:Riferimento"
            ),
            sqlparams=dict(
                Riferimento=picking.sale_id.name
                if picking.sale_id
                else picking.purchase_id.name
            ),
            metadata=None,
        )[0]
        # 4 whs lists of which 2 valid (stato=1) and 2 invalid (stato=3)
        self.assertEqual(len(whs_records2), len(whs_records) + list_len)
        for Elaborato in {x[0] for x in whs_records2}:
            # WHS cron change Elaborato to 2 in an un-controllable time
            self.assertIn(Elaborato, {5, 1, 2})
        return valid_whs_lists

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
        order1 = order_form1.save()
        order1.action_confirm()
        self.assertEqual(order1.state, "sale")
        picking1 = order1.picking_ids[0]
        self.assertEqual(len(picking1.move_lines.whs_list_ids), 1)
        if all(x.state == "assigned" for x in picking1.move_lines):
            self.assertEqual(picking1.state, "assigned")
        else:
            self.assertEqual(picking1.state, "waiting")
        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self._execute_select_all_valid_host_liste()
        self.assertEqual(len(whs_records), whs_len_records + 1)
        for whs_record in whs_records:
            self.assertTrue(order1.client_order_ref in whs_record._mapping.values())
            if self.product1.default_code in whs_record._mapping.values():
                self.assertTrue(
                    self.product1.customer_ids[0].product_code
                    in whs_record._mapping.values()
                )
            else:
                self.assertFalse(
                    self.product1.customer_ids[0].product_code
                    in whs_record._mapping.values()
                )
        # check cancel workflow
        whs_lists = picking1.move_lines.whs_list_ids
        self.assertEqual(len(whs_lists), 1)
        whs_list = whs_lists[0]
        self.assertEqual(whs_list.stato, "2")
        if all(x.state == "assigned" for x in picking1.move_lines):
            self.assertEqual(picking1.state, "assigned")
        else:
            self.assertEqual(picking1.state, "waiting")
        picking1.action_cancel()
        self.assertEqual(picking1.state, "cancel")
        # check whs lists are in stato '3' -> 'Da NON elaborare'
        self.assertEqual(picking1.move_lines.mapped("whs_list_ids.stato"), ["3"])
        # restore picking to assigned state
        picking1.action_back_to_draft()
        picking1.action_confirm()
        picking1.action_assign()
        whs_lists = picking1.move_lines.whs_list_ids.filtered(lambda x: x.stato != "3")
        self.assertEqual(len(whs_lists), 1)
        whs_list = whs_lists[0]
        self.assertTrue(whs_list)
        # check whs list is added, and only 1 valid whs list exists
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
            "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s, "
            "Lotto='%s', Lotto2='%s', Lotto3='%s', Lotto4='%s', Lotto5='%s' WHERE "
            "NumLista = '%s' AND NumRiga = '%s'"
            % (
                whs_list.qta,
                lotto,
                lotto2,
                lotto3,
                lotto4,
                lotto5,
                whs_list.num_lista,
                whs_list.riga,
            )
        )
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=sql_text(set_liste_elaborated_query), sqlparams=None, metadata=None
        )

        whs_select_query = (
            "SELECT Qta, QtaMovimentata, Lotto, Lotto3, Lotto3, Lotto4, Lotto5 "
            "FROM HOST_LISTE WHERE Elaborato = 4 AND "
            "NumLista = '%s' AND NumRiga = '%s'" % (whs_list.num_lista, whs_list.riga)
        )
        result_liste = self.dbsource.execute_mssql(
            sqlquery=sql_text(whs_select_query), sqlparams=None, metadata=None
        )
        self.assertEqual(
            str(result_liste[0]),
            "[(Decimal('5.000'), Decimal('5.000'), '55A1', '55A3', '55A3', '55A4', "
            "'55A5')]",
        )

        self.dbsource.whs_insert_read_and_synchronize_list()

        # check move and picking linked to sale order have changed state to done
        self.assertEqual(picking1.move_lines[0].state, "assigned")
        if all(x.state == "assigned" for x in picking1.move_lines):
            self.assertEqual(picking1.state, "assigned")
        else:
            self.assertEqual(picking1.state, "waiting")
        picking1.action_assign()
        if all(x.state == "assigned" for x in picking1.move_lines):
            self.assertEqual(picking1.state, "assigned")
        else:
            self.assertEqual(picking1.state, "waiting")
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
        for picking in order1.picking_ids:
            if all(x.state == "assigned" for x in picking.move_lines):
                self.assertEqual(picking.state, "assigned")
            else:
                self.assertEqual(picking.state, "waiting")
        picking = order1.picking_ids[0]
        self.assertEqual(len(picking.mapped("move_lines.whs_list_ids")), 2)

        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self.dbsource.execute_mssql(
            sqlquery=sql_text(
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
            self.assertTrue(order1.client_order_ref in whs_record._mapping.values())
            if self.product1.default_code in whs_record._mapping.values():
                self.assertTrue(
                    self.product1.customer_ids[0].product_code
                    in whs_record._mapping.values()
                )
            else:
                self.assertFalse(
                    self.product1.customer_ids[0].product_code
                    in whs_record._mapping.values()
                )

        whs_lists = self._check_cancel_workflow(picking, 2)
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self.dbsource.execute_mssql(
            sqlquery=sql_text(
                "SELECT Elaborato, NumLista, NumRiga FROM HOST_LISTE WHERE Qta!=:Qta"
            ),
            sqlparams=dict(Qta=0),
            metadata=None,
        )[0]
        self.assertEqual(len(whs_records), whs_len_records + 2)
        # simulate whs work: validate first move partially (3 over 5)
        self.dbsource.whs_insert_read_and_synchronize_list()
        set_liste_elaborated_query = (
            "UPDATE HOST_LISTE SET Elaborato=:Elaborato, "
            "QtaMovimentata=:QtaMovimentata WHERE NumLista=:NumLista AND "
            "NumRiga=:NumRiga"
        )
        for whs_list in whs_lists:
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(set_liste_elaborated_query),
                sqlparams=dict(
                    Elaborato=4,
                    QtaMovimentata=3,
                    NumLista=whs_list.num_lista,
                    NumRiga=whs_list.riga,
                ),
                metadata=None,
            )
        # do not launch self.dbsource.whs_insert_read_and_synchronize_list() here as it
        # would change Elaborato from 4 to 5, as it must do
        for whs_list in whs_lists:
            whs_select_query = (
                "SELECT Qta, QtaMovimentata, Priorita FROM HOST_LISTE WHERE "
                "Elaborato=:Elaborato AND NumLista=:NumLista AND NumRiga=:NumRiga"
            )
            result_liste = self.dbsource.execute_mssql(
                sqlquery=sql_text(whs_select_query),
                sqlparams=dict(
                    Elaborato=4, NumLista=whs_list.num_lista, NumRiga=whs_list.riga
                ),
                metadata=None,
            )
            self.assertIn(
                "[(Decimal('5.000'), Decimal('3.000'), 1)]", str(result_liste)
            )

        self.dbsource.whs_insert_read_and_synchronize_list()

        # check move and picking linked to sale order have changed state to done
        self.assertEqual(set(picking.move_lines.mapped("state")), {"assigned"})
        if all(x.state == "assigned" for x in picking.move_lines):
            self.assertEqual(picking.state, "assigned")
        else:
            self.assertEqual(picking.state, "waiting")
        self.assertAlmostEqual(picking.move_lines[0].move_line_ids[0].qty_done, 3.0)
        self.assertEqual(picking.state, "assigned")

        # simulate user partial validate of picking and check backorder exist
        res = picking.button_validate()
        Form(self.env[res["res_model"]].with_context(res["context"])).save().process()
        backorder_picking = order1.picking_ids - picking
        # Simulate whs user validation
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_lists = backorder_picking.mapped("move_lines.whs_list_ids").filtered(
            lambda x: x.stato != "3"
        )
        for whs_list in whs_lists:
            # simulate whs work: total process
            set_liste_elaborated_query = (
                "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s WHERE "
                "NumLista = '%s' AND NumRiga = '%s'"
                % (whs_list.qta, whs_list.num_lista, whs_list.riga)
            )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(set_liste_elaborated_query),
                sqlparams=None,
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
            sqlquery=sql_text(
                "SELECT * FROM HOST_LISTE WHERE Elaborato!=:Elaborato AND Qta!=:Qta"
            ),
            sqlparams=dict(Elaborato=5, Qta=0),
            metadata=None,
        )[0]
        self.assertEqual(len(whs_records), whs_len_records + 2)
        for whs_record in whs_records:
            self.assertTrue(order1.client_order_ref in whs_record._mapping.values())
            if self.product1.default_code in whs_record._mapping.values():
                self.assertTrue(
                    self.product1.customer_ids[0].product_code
                    in whs_record._mapping.values()
                )
            else:
                self.assertFalse(
                    self.product1.customer_ids[0].product_code
                    in whs_record._mapping.values()
                )

        # check backorder is not created without whs list validation
        res = picking.button_validate()
        Form(self.env[res["res_model"]].with_context(res["context"])).save().process()
        # Check user cannot create backorder if whs list is not processed on whs system
        # TODO NON QUI PERÒ: check backorder is created for residual
        self.assertNotEqual(picking.state, "done")
        self.assertEqual(len(order1.picking_ids), 1)

        whs_lists = picking.mapped("move_lines.whs_list_ids")
        for whs_list in whs_lists:
            # simulate whs work: partial processing (3 of 5) of product #1
            # and total (20 of 20) of product #2 so it is -4 on warehouse
            set_liste_elaborated_query = (
                "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s WHERE "
                "NumLista = '%s' AND NumRiga = '%s'"
                % (
                    3 if whs_list.product_id == self.product1 else 20,
                    whs_list.num_lista,
                    whs_list.riga,
                )
            )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(set_liste_elaborated_query),
                sqlparams=None,
                metadata=None,
            )
        # check whs work is done correctly
        for whs_list in whs_lists:
            whs_select_query = (
                "SELECT Qta, QtaMovimentata, Priorita FROM HOST_LISTE WHERE Elaborato "
                "= 4 AND NumLista = '%s' AND NumRiga = '%s'"
                % (whs_list.num_lista, whs_list.riga)
            )
            result_liste = self.dbsource.execute_mssql(
                sqlquery=sql_text(whs_select_query), sqlparams=None, metadata=None
            )
            self.assertEqual(
                str(result_liste[0]),
                "[(Decimal('5.000'), Decimal('3.000'), 2)]"
                if whs_list.product_id == self.product1
                else "[(Decimal('20.000'), Decimal('20.000'), 2)]",
            )

        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(set(picking.move_lines.mapped("state")), {"assigned"})
        self.assertEqual(
            picking.move_lines.filtered(
                lambda move: move.product_id == self.product1
            ).move_line_ids.qty_done,
            3.0,
        )
        self.assertEqual(
            picking.move_lines.filtered(
                lambda move: move.product_id == self.product2
            ).move_line_ids.qty_done,
            20.0,
        )
        picking.action_assign()
        # Do not run self.run_stock_procurement_scheduler() here as it will override
        # quantity_done in picking.move_lines as the availability differs from quantity
        # set manually!
        self.assertEqual(picking.state, "assigned")

        res = picking.button_validate()
        Form(self.env[res["res_model"]].with_context(res["context"])).save().process()
        self.assertEqual(picking.state, "done")
        # check back picking is waiting as Odoo qty is not considered
        self.assertEqual(len(order1.picking_ids), 2)
        backorder_picking = order1.picking_ids - picking
        self.assertEqual(backorder_picking.move_lines.mapped("state"), ["assigned"])
        # todo check also a 'partially_available'
        self.assertEqual(backorder_picking.state, "assigned")

        self.dbsource.whs_insert_read_and_synchronize_list()
        back_whs_list = backorder_picking.mapped("move_lines.whs_list_ids")
        whs_select_query = (
            "SELECT Qta, QtaMovimentata FROM HOST_LISTE WHERE "
            "NumLista = '%s' AND NumRiga = '%s'"
            % (back_whs_list.num_lista, back_whs_list.riga)
        )
        result_liste = self.dbsource.execute_mssql(
            sqlquery=sql_text(whs_select_query), sqlparams=None, metadata=None
        )
        self.assertEqual(str(result_liste[0]), "[(Decimal('2.000'), None)]")

        # simulate whs work set done to rest of backorder
        set_liste_elaborated_query = (
            "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s WHERE "
            "NumLista = '%s' AND NumRiga = '%s'"
            % (2, back_whs_list.num_lista, back_whs_list.riga)
        )
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=sql_text(set_liste_elaborated_query), sqlparams=None, metadata=None
        )

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

        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self._execute_select_all_valid_host_liste()
        self.assertEqual(len(whs_records), whs_len_records + 4)
        for whs_record in whs_records:
            self.assertTrue(order1.client_order_ref in whs_record._mapping.values())
            if self.product1.default_code in whs_record._mapping.values():
                self.assertTrue(
                    self.product1.customer_ids[0].product_code
                    in whs_record._mapping.values()
                )
            else:
                self.assertFalse(
                    self.product1.customer_ids[0].product_code
                    in whs_record._mapping.values()
                )
        # simulate whs work: validate first move totally and second move partially
        whs_lists = picking.mapped("move_lines.whs_list_ids")
        for whs_list in whs_lists:
            # simulate whs work: total process
            set_liste_elaborated_query = (
                "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s WHERE "
                "NumLista = '%s' AND NumRiga = '%s'"
                % (
                    0 if whs_list.product_id == self.product3 else 5,
                    whs_list.num_lista,
                    whs_list.riga,
                )
            )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(set_liste_elaborated_query),
                sqlparams=None,
                metadata=None,
            )

        for whs_l in whs_lists:
            whs_select_query = (
                "SELECT Qta, QtaMovimentata, Priorita FROM HOST_LISTE WHERE Elaborato"
                " = 4 AND NumLista = '%s' AND NumRiga = '%s'"
                % (whs_l.num_lista, whs_l.riga)
            )
            result_liste = self.dbsource.execute_mssql(
                sqlquery=sql_text(whs_select_query), sqlparams=None, metadata=None
            )
            self.assertEqual(
                str(result_liste[0]),
                "[(Decimal('5.000'), Decimal('5.000'), 0)]"
                if whs_l.product_id == self.product1
                else "[(Decimal('10.000'), Decimal('5.000'), 0)]"
                if whs_l.product_id == self.product2
                else "[(Decimal('20.000'), Decimal('0.000'), 0)]"
                if whs_l.product_id == self.product3
                else "[(Decimal('20.000'), Decimal('5.000'), 0)]",
            )

        self.dbsource.whs_insert_read_and_synchronize_list()

        # check move and picking linked to sale order have changed state to done
        for move_line in picking.move_lines:
            self.assertEqual(
                move_line.state,
                "assigned"
                if move_line.product_id in [self.product1, self.product3]
                else "confirmed"
                if move_line.product_id == self.product4
                else "partially_available",
            )
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
        self.assertEqual(picking.state, "confirmed")
        picking.action_assign()
        self.assertEqual(picking.state, "assigned")

        # simulate user partial validate of picking and check backorder exist
        res = picking.button_validate()
        self.assertEqual(picking.state, "assigned")
        backorder_wiz = Form(
            self.env[res["res_model"]].with_context(res["context"])
        ).save()
        # User must set correctly quantity as set by WHS user, ignoring qty set
        # automatically by Odoo, so check that error is raised without intervention
        with self.assertRaises(UserError):
            backorder_wiz.process()
        for move_line in picking.move_lines.filtered(
            lambda x: x.product_id != self.product3
        ):
            move_line.quantity_done = 5
        # Simulate whs user partial picking validation
        whs_lists = picking.mapped("move_lines.whs_list_ids")
        for whs_list in whs_lists.filtered(lambda x: x.product_id != self.product3):
            # simulate whs work: no processing of product #3
            # and partial of product #1,2,4
            set_liste_elaborated_query = (
                "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=:QtaMovimentata "
                "WHERE NumLista=:NumLista AND NumRiga=:NumRiga"
            )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(set_liste_elaborated_query),
                sqlparams=dict(
                    QtaMovimentata=5, NumLista=whs_list.num_lista, NumRiga=whs_list.riga
                ),
                metadata=None,
            )
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(sum(picking.move_lines.mapped("quantity_done")), 15)
        res = picking.button_validate()
        backorder_wiz = Form(
            self.env[res["res_model"]].with_context(res["context"])
        ).save()
        backorder_wiz.process()
        self.assertEqual(picking.state, "done")
        # check backorder whs list has the correct qty
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

        # Simulate whs user validation
        whs_lists = picking.mapped("move_lines.whs_list_ids")
        for whs_list in whs_lists:
            # simulate whs work: total process
            set_liste_elaborated_query = (
                "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=:QtaMovimentata "
                "WHERE NumLista=:NumLista AND NumRiga=:NumRiga"
            )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(set_liste_elaborated_query),
                sqlparams=dict(
                    QtaMovimentata=whs_list.qta,
                    NumLista=whs_list.num_lista,
                    NumRiga=whs_list.riga,
                ),
                metadata=None,
            )

        self.dbsource.whs_insert_read_and_synchronize_list()
        # check whs list for backorder is not created as the first is completed entirely
        # FIXME: what does the note above mean?
        res = self._execute_select_all_valid_host_liste()
        self.assertEqual(len(res), whs_len_records + 6)
        # self.run_stock_procurement_scheduler()
        backorder_picking.action_assign()
        for move_line in backorder_picking.move_lines:
            state = "confirmed"
            if move_line.product_id.qty_available > 0:
                state = "assigned"
            self.assertEqual(move_line.state, state)

    def _execute_select_all_valid_host_liste(self):
        # insert lists in WHS: this has to be invoked before every sql call!
        self.dbsource.whs_insert_read_and_synchronize_list()
        res = self.dbsource.execute_mssql(
            sqlquery=sql_text("SELECT * FROM HOST_LISTE WHERE Qta!=:Qta"),
            sqlparams=dict(Qta=0),
            metadata=None,
        )[0]
        return res

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

        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            whs_len_records + 2,
        )
        # controlla che le liste whs siano annullate (impostate con Qta=0)
        order1.action_cancel()
        # insert lists in WHS: this has to be invoked before every sql call!
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
        self.assertEqual(picking.move_lines.whs_list_ids.mapped("stato"), ["1", "1"])
        # insert lists in WHS: this has to be invoked before every sql call, but not
        # before a select for a check, as it change Elaborato from 4 to 5
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            whs_len_records + 2,
        )
        # self.run_stock_procurement_scheduler()
        picking.action_assign()
        if all(x.state == "assigned" for x in picking.move_lines):
            self.assertEqual(picking.state, "assigned")
        else:
            self.assertEqual(picking.state, "cancel")
        hyddemo_whs_lists = picking.mapped("move_lines.whs_list_ids")
        lists = {x.riga: x.num_lista for x in hyddemo_whs_lists}
        # simulate launch from WHS user
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
            sqlquery=sql_text(set_liste_elaborating_query),
            sqlparams=None,
            metadata=None,
        )
        with self.assertRaises(UserError):
            order1.action_cancel()
        # Check product added to sale order after confirmation create new whs lists
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

    def test_05_repair(self):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()

        whs_len_records = len(self._execute_select_all_valid_host_liste())
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
        self.assertEqual(
            repair.state, "confirmed", 'Repair order should be in "Confirmed" state.'
        )
        repair.action_repair_start()
        self.assertEqual(
            repair.state,
            "under_repair",
            'Repair order should be in "Under_repair" state.',
        )
        repair.action_repair_end()
        self.assertEqual(
            repair.state, "done", 'Repair order should be in "Done" state.'
        )
        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(
                self.dbsource.execute_mssql(
                    sqlquery=sql_text(
                        "SELECT * FROM HOST_LISTE WHERE Elaborato!=:Elaborato AND "
                        "Qta!=:Qta"
                    ),
                    sqlparams=dict(Elaborato=5, Qta=0),
                    metadata=None,
                )[0]
            ),
            whs_len_records + 2,
        )

        # simulate whs work: partial processing of product #2
        # and total of product #3
        whs_lists = repair.mapped("operations.move_id.whs_list_ids")
        for whs_list in whs_lists:
            set_liste_elaborated_query = (
                "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s WHERE "
                "NumLista = '%s' AND NumRiga = '%s'"
                % (
                    2 if whs_list.product_id == self.product2 else 3,
                    whs_list.num_lista,
                    whs_list.riga,
                )
            )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(set_liste_elaborated_query),
                sqlparams=None,
                metadata=None,
            )

        for whs_list in whs_lists:
            whs_select_query = (
                "SELECT Qta, QtaMovimentata FROM HOST_LISTE WHERE Elaborato = 4 AND "
                "NumLista = '%s' AND NumRiga = '%s'"
                % (whs_list.num_lista, whs_list.riga)
            )
            result_liste = self.dbsource.execute_mssql(
                sqlquery=sql_text(whs_select_query), sqlparams=None, metadata=None
            )
            self.assertEqual(
                str(result_liste[0]),
                "[(Decimal('5.000'), Decimal('2.000'))]"
                if whs_list.product_id == self.product2
                else "[(Decimal('3.000'), Decimal('3.000'))]",
            )

        # this update Odoo from WHS
        self.dbsource.whs_insert_read_and_synchronize_list()
        # check whs_list are elaborated
        for whs_list in whs_lists:
            whs_select_query = (
                "SELECT Qta, QtaMovimentata FROM HOST_LISTE WHERE Elaborato = 5 AND "
                "NumLista = '%s' AND NumRiga = '%s'"
                % (whs_list.num_lista, whs_list.riga)
            )
            result_liste = self.dbsource.execute_mssql(
                sqlquery=sql_text(whs_select_query), sqlparams=None, metadata=None
            )
            self.assertIn(
                "[(Decimal('5.000'), Decimal('2.000'))]"
                if whs_list.product_id == self.product2
                else "[(Decimal('3.000'), Decimal('3.000'))]",
                str(result_liste),
            )

    def test_06_purchase(self):
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
        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            whs_len_records + 2,
        )

        # simulate whs work: partial processing of product #2
        # and total of product #3
        whs_lists = purchase.mapped("picking_ids.move_lines.whs_list_ids")
        for whs_list in whs_lists:
            set_liste_elaborated_query = (
                "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s WHERE "
                "NumLista = '%s' AND NumRiga = '%s'"
                % (
                    2 if whs_list.product_id == self.product2 else 3,
                    whs_list.num_lista,
                    whs_list.riga,
                )
            )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(set_liste_elaborated_query),
                sqlparams=None,
                metadata=None,
            )

        for whs_list in whs_lists:
            whs_select_query = (
                "SELECT Qta, QtaMovimentata FROM HOST_LISTE WHERE Elaborato = 4 AND "
                "NumLista = '%s' AND NumRiga = '%s'"
                % (whs_list.num_lista, whs_list.riga)
            )
            result_liste = self.dbsource.execute_mssql(
                sqlquery=sql_text(whs_select_query), sqlparams=None, metadata=None
            )
            self.assertEqual(
                str(result_liste[0]),
                "[(Decimal('20.000'), Decimal('2.000'))]"
                if whs_list.product_id == self.product2
                else "[(Decimal('3.000'), Decimal('3.000'))]",
            )

        # this update Odoo from WHS
        self.dbsource.whs_insert_read_and_synchronize_list()
        # check whs_list are elaborated
        for whs_list in whs_lists:
            whs_select_query = (
                "SELECT Qta, QtaMovimentata FROM HOST_LISTE WHERE Elaborato = 5 AND "
                "NumLista = '%s' AND NumRiga = '%s'"
                % (whs_list.num_lista, whs_list.riga)
            )
            result_liste = self.dbsource.execute_mssql(
                sqlquery=sql_text(whs_select_query), sqlparams=None, metadata=None
            )
            self.assertEqual(
                str(result_liste[0]),
                "[(Decimal('20.000'), Decimal('2.000'))]"
                if whs_list.product_id == self.product2
                else "[(Decimal('3.000'), Decimal('3.000'))]",
            )

        # simulate user partial validate of picking and check backorder exist
        picking = purchase.picking_ids[0]
        # self.run_stock_procurement_scheduler()
        picking.action_assign()
        if all(x.state == "assigned" for x in picking.move_lines):
            self.assertEqual(picking.state, "assigned")
        else:
            self.assertEqual(picking.state, "waiting")
        # check that action_assign run by scheduler do not change state
        # self.assertEqual(picking.state, "assigned")
        # picking.action_pack_operation_auto_fill() FIXME check what this method do
        res = picking.button_validate()
        Form(self.env[res["res_model"]].with_context(res["context"])).save().process()
        self.assertEqual(picking.state, "done")

        # check back picking is waiting as waiting for WHS work
        self.assertEqual(len(purchase.picking_ids), 2)
        backorder_picking = purchase.picking_ids - picking
        # self.run_stock_procurement_scheduler()
        backorder_picking.action_assign()
        if all(x.state == "assigned" for x in backorder_picking.move_lines):
            self.assertEqual(backorder_picking.state, "assigned")

        # check whs_list for backorder is created
        self.dbsource.whs_insert_read_and_synchronize_list()
        back_whs_list = backorder_picking.mapped("move_lines.whs_list_ids")
        whs_select_query = (
            "SELECT Qta, QtaMovimentata FROM HOST_LISTE WHERE "
            "NumLista = '%s' AND NumRiga = '%s'"
            % (back_whs_list.num_lista, back_whs_list.riga)
        )
        result_liste = self.dbsource.execute_mssql(
            sqlquery=sql_text(whs_select_query), sqlparams=None, metadata=None
        )
        self.assertEqual(str(result_liste[0]), "[(Decimal('18.000'), None)]")
        # TODO check cancel workflow without action_assign that create whs list anyway
        self._check_cancel_workflow(backorder_picking, 1)
        backorder_picking.action_assign()
        # simulate whs work set done to rest of backorder
        set_liste_elaborated_query = (
            "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s WHERE "
            "NumLista = '%s' AND NumRiga = '%s'"
            % (18, back_whs_list.num_lista, back_whs_list.riga)
        )
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=sql_text(set_liste_elaborated_query), sqlparams=None, metadata=None
        )

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
        # Check product added to purchase order after confirm create whs list with
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
        whs_select_query = (
            "SELECT Qta, QtaMovimentata FROM HOST_LISTE WHERE "
            "NumLista = '%s' AND NumRiga = '%s'"
            % (po_whs_list.num_lista, po_whs_list.riga)
        )
        result_liste = self.dbsource.execute_mssql(
            sqlquery=sql_text(whs_select_query), sqlparams=None, metadata=None
        )
        # whs list is created for the increased qty
        self.assertEqual(str(result_liste[0]), "[(Decimal('7.000'), None)]")
