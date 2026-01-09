import os

from odoo import _, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import Form
from odoo.tools import relativedelta

from odoo.addons.connector_whs.models.base_external_dbsource import clean_sql_text
from odoo.addons.connector_whs.tests.test_connector_wms import CommonConnectorWMS

from ..models.hyddemo_whs_liste import tipo_operazione_dict


@tagged("-standard", "test_wms")
class TestConnectorWmsModula(CommonConnectorWMS):
    def setUp(self):
        super().setUp()
        dbsource_name = "Odoo WMS local server"
        dbsource = self.dbsource_model.search([("name", "=", dbsource_name)])
        if not dbsource:
            conn_file = os.path.join(
                os.path.expanduser("~"), "connection_wms_modula.txt"
            )
            if not os.path.isfile(conn_file):
                raise UserError(_("Missing connection string!"))
            with open(conn_file) as file:
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
                }
            )
        self.dbsource = dbsource
        self.warehouse = self.env["stock.warehouse"].search(
            [
                ("company_id", "=", self.env.user.company_id.id),
            ]
        )
        self.warehouse = self.warehouse.with_context(do_not_check_quant=True)
        self.step_delivery = ""
        self._clean_all()

    def _configure_1_step_delivery(self):
        self.warehouse.delivery_steps = "ship_only"
        self.warehouse.manufacture_steps = "mrp_one_step"
        self.dbsource.write(
            {
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
                            ]
                        )
                        .ids,
                    )
                ]
            }
        )
        self.step_delivery = "one"

    def _configure_2_steps_delivery(self):
        self.warehouse.delivery_steps = "pick_ship"
        self.warehouse.manufacture_steps = "pbm"
        self.dbsource.write(
            {
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
                                ("id", "!=", self.warehouse.out_type_id.id),
                            ]
                        )
                        .ids,
                    )
                ]
            }
        )
        self.step_delivery = "two"

    def _clean_all(self):
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=clean_sql_text("DELETE FROM IMP_ORDINI_RIGHE"),
            sqlparams=None,
            metadata=None,
        )
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=clean_sql_text("DELETE FROM IMP_ORDINI"),
            sqlparams=None,
            metadata=None,
        )
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=clean_sql_text("DELETE FROM EXP_ORDINI_RIGHE"),
            sqlparams=None,
            metadata=None,
        )
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=clean_sql_text("DELETE FROM EXP_ORDINI"),
            sqlparams=None,
            metadata=None,
        )

    def _select_wms_liste(self, wms_list, db_type="EXP"):
        return self.dbsource.execute_mssql(
            sqlquery=clean_sql_text(
                f"SELECT RIG_QTAR {', RIG_QTAE' if db_type == 'EXP' else ''} "
                f"FROM {db_type}_ORDINI_RIGHE WHERE "
                "RIG_ORDINE=:RIG_ORDINE AND RIG_HOSTINF=:RIG_HOSTINF"
            ),
            sqlparams=dict(RIG_ORDINE=wms_list.num_lista, RIG_HOSTINF=wms_list.riga),
            metadata=None,
        )

    def _check_cancel_workflow(self, picking, list_len):
        """
        This method is used to check the re-use of the same WMS list linked to the
        picking when this is cancelled, without re-creating a new one.
        """
        whs_lists = picking.mapped("move_lines.whs_list_ids")
        num_liste = whs_lists.mapped("num_lista")
        self.assertEqual(len(whs_lists), list_len)
        self.assertEqual(set(whs_lists.mapped("stato")), {"2"})
        self.assertEqual(set(whs_lists.mapped("qtamov")), {0.0})
        picking.action_assign()
        # todo if it's a purchase it's assigned
        self.assertEqual(picking.state, "assigned")
        picking.action_cancel()
        # check WMS lists are deleted
        self.assertEqual(picking.state, "cancel")
        self.assertFalse(picking.mapped("move_lines.whs_list_ids"))
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records1 = self.dbsource.execute_mssql(
            sqlquery=clean_sql_text(
                "SELECT RIG_ORDINE, RIG_HOSTINF FROM EXP_ORDINI_RIGHE "
                "WHERE RIG_ORDINE IN :RIG_ORDINE"
            ),
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
        # check new WMS lists are present
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records2 = self.dbsource.execute_mssql(
            sqlquery=clean_sql_text(
                "SELECT RIG_ORDINE, RIG_HOSTINF FROM IMP_ORDINI_RIGHE "
                "WHERE RIG_ORDINE IN :RIG_ORDINE"
            ),
            sqlparams=dict(RIG_ORDINE=valid_whs_lists.mapped("num_lista")),
            metadata=None,
        )[0]
        self.assertEqual(
            len(whs_records2), list_len, "There must exist 2 valid WMS records!"
        )
        return valid_whs_lists

    def _execute_select_all_valid_host_liste(self):
        # insert lists in WMS: this has to be invoked before every sql call!
        self.dbsource.whs_insert_read_and_synchronize_list()
        res = self.dbsource.execute_mssql(
            sqlquery=clean_sql_text(
                "SELECT RIG_ORDINE, RIG_HOSTINF, RIG_ARTICOLO, RIG_QTAR "
                "FROM IMP_ORDINI_RIGHE WHERE RIG_QTAR!=:RIG_QTAR"
            ),
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
            current_whs_lists = whs_lists.filtered(
                lambda x, nl=num_lista: x.num_lista == nl
            )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=clean_sql_text(
                    "INSERT INTO EXP_ORDINI "
                    "(ORD_ORDINE, ORD_TIPOOP, ORD_DES) VALUES "
                    "(:ORD_ORDINE, :ORD_TIPOOP, :ORD_DES)"
                ),
                sqlparams=dict(
                    ORD_ORDINE=num_lista,
                    ORD_TIPOOP=tipo_operazione_dict[current_whs_lists[0].tipo],
                    ORD_DES="%s - %s"[:50]
                    % (
                        current_whs_lists[0].riferimento
                        if current_whs_lists[0].riferimento
                        else "",
                        current_whs_lists[0].ragsoc
                        if current_whs_lists[0].ragsoc
                        else "",
                    ),
                ),
                metadata=None,
            )
            for whs_list in current_whs_lists:
                self.dbsource.with_context(no_return=True).execute_mssql(
                    sqlquery=clean_sql_text(
                        "INSERT INTO EXP_ORDINI_RIGHE "
                        "(RIG_ORDINE, RIG_HOSTINF, RIG_ARTICOLO, RIG_QTAR, RIG_QTAE) "
                        "VALUES "
                        "(:RIG_ORDINE, :RIG_HOSTINF, :RIG_ARTICOLO, :RIG_QTAR, "
                        ":RIG_QTAE)"
                    ),
                    sqlparams=dict(
                        RIG_ORDINE=whs_list.num_lista,
                        RIG_HOSTINF=whs_list.riga,
                        RIG_ARTICOLO=whs_list.product_id.default_code[:50]
                        if whs_list.product_id.default_code
                        else "prodotto %s senza codice" % whs_list.product_id.id,
                        RIG_QTAR=whs_list.qta,
                        RIG_QTAE=whs_lists_dict[whs_list],
                    ),
                    metadata=None,
                )
        for num_lista in set(whs_lists.mapped("num_lista")):
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=clean_sql_text(
                    "DELETE FROM IMP_ORDINI_RIGHE WHERE RIG_ORDINE=:RIG_ORDINE"
                ),
                sqlparams=dict(RIG_ORDINE=num_lista),
                metadata=None,
            )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=clean_sql_text(
                    "DELETE FROM IMP_ORDINI WHERE ORD_ORDINE=:ORD_ORDINE"
                ),
                sqlparams=dict(ORD_ORDINE=num_lista),
                metadata=None,
            )

    def _test_00_complete_picking_from_sale(self):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()
        self._clean_all()
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
        picking1 = order1.picking_ids.filtered(
            lambda x: x.picking_type_id
            == (
                self.warehouse.out_type_id
                if self.step_delivery == "one"
                else self.warehouse.pick_type_id
            )
        )
        self.assertEqual(len(picking1.mapped("move_lines.whs_list_ids")), 1)
        self.assertEqual(
            picking1.mapped("move_lines.whs_list_ids")[0].ragsoc, order1.partner_id.name
        )
        if all(x.state == "assigned" for x in picking1.move_lines):
            self.assertEqual(picking1.state, "assigned")
        else:
            self.assertIn(picking1.state, ["waiting", "confirmed"])
        # check WMS list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self._execute_select_all_valid_host_liste()
        self.assertEqual(len(whs_records), 1)
        # RIG_ORDINE, RIG_HOSTINF, RIG_ARTICOLO, RIG_QTAR
        for whs_record in whs_records:
            lista = whs_record[0]
            default_code = whs_record[2]
            qty = whs_record[3]
            line = order1.order_line.filtered(
                lambda x: not x.product_id.exclude_from_whs
            )
            move_line = picking1.move_lines.filtered(
                lambda x: not x.product_id.exclude_from_whs
            )
            self.assertEqual(default_code, line.product_id.default_code)
            self.assertEqual(qty, line.product_uom_qty)
            self.assertEqual(qty, move_line.whs_list_ids.qta)
            self.assertEqual(lista, move_line.whs_list_ids.num_lista)
        # check cancel workflow
        whs_lists = picking1.mapped("move_lines.whs_list_ids")
        self.assertEqual(len(whs_lists), 1)
        self.assertEqual(whs_lists.stato, "2")
        if all(x.state == "assigned" for x in picking1.move_lines):
            self.assertEqual(picking1.state, "assigned")
        else:
            self.assertEqual(picking1.state, "confirmed")
        picking1.action_cancel()
        self.assertEqual(picking1.state, "cancel")
        # check WMS lists are unlinked (only with a working WMS software they could be
        # in stato '3' -> 'Da NON elaborare' after elaboration)
        self.assertFalse(picking1.move_lines.mapped("whs_list_ids"))
        # restore picking to assigned state
        picking1.action_back_to_draft()
        picking1.action_confirm()
        picking1.action_assign()
        whs_lists = picking1.mapped("move_lines.whs_list_ids").filtered(
            lambda x: x.stato != "3"
        )
        self.assertEqual(len(whs_lists), 1)
        # check WMS list is added, and only 1 valid WMS list exists
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self._execute_select_all_valid_host_liste()
        self.assertEqual(len(whs_records), 1)
        self.simulate_wms_cron({x: x.qta for x in whs_lists})

        result_liste = self._select_wms_liste(whs_lists)
        self.assertEqual(str(result_liste[0]), "[(Decimal('5.000'), Decimal('5.000'))]")

        self.dbsource.whs_insert_read_and_synchronize_list()

        # check move and picking linked to sale order have changed state to done
        self.assertEqual(
            picking1.move_lines.filtered(
                lambda x: not x.product_id.exclude_from_whs
            ).state,
            "assigned",
        )
        self.assertEqual(picking1.state, "assigned")

    def _test_01_partial_picking_from_sale(self):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()
        self._clean_all()
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
        self.assertEqual(order1.state, "sale")
        if self.step_delivery == "one":
            self.assertEqual(len(order1.picking_ids), 1)
            picking = order1.picking_ids
            self.assertIn(picking.state, ["assigned", "confirmed"])
        else:
            self.assertEqual(len(order1.picking_ids), 2)
            picking = order1.picking_ids.filtered(
                lambda x: x.picking_type_id == self.warehouse.pick_type_id
            )
            self.assertIn(picking.state, ["assigned", "confirmed"])
        # sale order lines for the same product are merged
        self.assertEqual(sum(picking.mapped("move_lines.whs_list_ids.qta")), 10)
        self.assertEqual(
            picking.mapped("move_lines.whs_list_ids")[0].ragsoc, order1.partner_id.name
        )
        self.assertEqual(
            len(set(picking.mapped("move_lines.whs_list_ids.num_lista"))), 1
        )

        # check WMS list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        # lists are not processed in Modula now, so do not launch simulate_wms_cron() as
        # it do the whole process (import from Host to Modula, process by user, export
        # from Modula to Host)
        self.assertEqual(set(picking.mapped("move_lines.whs_list_ids.stato")), {"2"})
        whs_lists = self._check_cancel_workflow(
            picking, 2 if self.step_delivery == "one" else 1
        )
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self.dbsource.execute_mssql(
            sqlquery=clean_sql_text(
                "SELECT RIG_ORDINE, RIG_HOSTINF FROM IMP_ORDINI_RIGHE "
                "WHERE RIG_QTAR!=:RIG_QTAR"
            ),
            sqlparams=dict(RIG_QTAR=0),
            metadata=None,
        )[0]
        self.assertEqual(len(whs_records), 2 if self.step_delivery == "one" else 1)
        # simulate WMS work: validate first move partially (3 over 5)
        self.dbsource.whs_insert_read_and_synchronize_list()
        if self.step_delivery == "one":
            self.simulate_wms_cron({x: 3 for x in whs_lists})
        else:
            self.simulate_wms_cron({x: 6 for x in whs_lists})
        for whs_list in whs_lists:
            result_liste = self._select_wms_liste(whs_list)
            if self.step_delivery == "one":
                self.assertIn(
                    "[(Decimal('5.000'), Decimal('3.000'))]", str(result_liste)
                )
            else:
                self.assertIn(
                    "[(Decimal('10.000'), Decimal('6.000'))]", str(result_liste)
                )
        self.dbsource.whs_insert_read_and_synchronize_list()
        # check move and picking linked to sale order have changed state to done
        self.assertEqual(picking.state, "assigned")
        self.assertAlmostEqual(
            sum(picking.mapped("move_lines.move_line_ids.qty_done")), 6.0
        )

        # simulate user partial validate of picking and check backorder exist
        res = picking.button_validate()
        Form(self.env[res["res_model"]].with_context(**res["context"])).save().process()
        # Create backorder: 1 WMS list of 2 is partially processed
        if self.step_delivery == "one":
            backorder_picking = (
                order1.picking_ids.filtered(lambda x: not x.state == "cancel") - picking
            )
        else:
            backorder_picking = (
                order1.picking_ids.filtered(
                    lambda x: not x.state == "cancel"
                    and x.picking_type_id == self.warehouse.pick_type_id
                )
                - picking
            )
        # Simulate WMS user validation
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_lists = backorder_picking.mapped("move_lines.whs_list_ids").filtered(
            lambda x: x.stato != "3"
        )
        # simulate WMS work: total process
        self.simulate_wms_cron({x: x.qta for x in whs_lists})

        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertFalse(
            self._execute_select_all_valid_host_liste(),
            "Imported lists are not deleted!",
        )

        # check backorder picking is waiting for WMS process
        if self.step_delivery == "one":
            self.assertEqual(len(order1.picking_ids), 2)
        else:
            self.assertEqual(len(order1.picking_ids), 3)
        if self.step_delivery == "one":
            self.assertEqual(backorder_picking.state, "confirmed")

    def _test_02_partial_picking_partial_available_from_sale(self):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()
        self._clean_all()
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
        self.assertEqual(order1.state, "sale")
        if self.step_delivery == "one":
            self.assertEqual(len(order1.picking_ids), 1)
            picking = order1.picking_ids
        else:
            self.assertEqual(len(order1.picking_ids), 2)
            picking = order1.picking_ids.filtered(
                lambda x: x.picking_type_id == self.warehouse.pick_type_id
            )
        self.assertEqual(len(picking.mapped("move_lines.whs_list_ids")), 2)
        self.assertEqual(picking.state, "assigned")

        # check WMS list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        # self.simulate_wms_cron(
        #     {x: x.qta for x in picking.mapped('move_lines.whs_list_ids')})
        whs_records = self.dbsource.execute_mssql(
            sqlquery=clean_sql_text(
                "SELECT RIG_ORDINE, RIG_HOSTINF, RIG_ARTICOLO, RIG_QTAR "
                "FROM IMP_ORDINI_RIGHE WHERE RIG_QTAR!=:RIG_QTAR"
            ),
            sqlparams=dict(RIG_QTAR=0),
            metadata=None,
        )[0]
        self.assertEqual(len(whs_records), 2)
        res = picking.button_validate()
        # check backorder is not created without WMS list validation
        # User cannot create backorder if WMS list is not processed on WMS system
        if self.step_delivery == "one":
            Form(
                self.env[res["res_model"]].with_context(**res["context"])
            ).save().process()
        self.assertNotEqual(picking.state, "done")
        if self.step_delivery == "one":
            self.assertEqual(len(order1.picking_ids), 1)
            picking = order1.picking_ids
        else:
            self.assertEqual(len(order1.picking_ids), 2)
            picking = order1.picking_ids.filtered(
                lambda x: x.picking_type_id == self.warehouse.pick_type_id
            )

        whs_lists = picking.mapped("move_lines.whs_list_ids")
        # simulate WMS work: partial processing (3 of 5) of product #1
        # and total (20 of 20) of product #2, so it is -4 on warehouse
        self.simulate_wms_cron(
            {x: 3 if x.product_id == self.product1 else 20 for x in whs_lists}
        )
        # check WMS work is done correctly
        for whs_list in whs_lists:
            result_liste = self._select_wms_liste(whs_list)
            self.assertEqual(
                str(result_liste[0]),
                "[(Decimal('5.000'), Decimal('3.000'))]"
                if whs_list.product_id == self.product1
                else "[(Decimal('20.000'), Decimal('20.000'))]",
            )

        self.dbsource.whs_insert_read_and_synchronize_list()
        self.simulate_wms_cron(
            {x: x.qta for x in picking.mapped("move_lines.whs_list_ids")}
        )
        # check move and picking linked to sale order have changed state to done
        self.assertEqual(
            picking.move_lines.filtered(
                lambda x: x.product_id == self.product1 and x.quantity_done == 3
            ).state,
            "assigned",
        )
        self.assertAlmostEqual(
            sum(picking.mapped("move_lines.move_line_ids.qty_done")), 23.0
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
            self.env[res["res_model"]].with_context(**res["context"])
        ).save()
        # User cannot create backorder if WMS list is not processed on WMS system
        #
        # TODO: check backorder is created for residual
        backorder_wiz.process()
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(picking.state, "done")

        # check back picking is waiting as Odoo qty is not considered
        if self.step_delivery == "one":
            self.assertEqual(len(order1.picking_ids), 2)
            backorder_picking = order1.picking_ids - picking
        else:
            self.assertEqual(len(order1.picking_ids), 3)
            backorder_picking = (
                order1.picking_ids.filtered(
                    lambda x: x.picking_type_id == self.warehouse.pick_type_id
                )
                - picking
            )
        # check whs_list for backorder is created
        back_whs_list = backorder_picking.mapped("move_lines.whs_list_ids")
        self.assertTrue(back_whs_list)
        # self.assertEqual(backorder_picking.move_lines.mapped("state"), ["assigned"])
        # todo check also a 'partially_available'
        # self.assertEqual(backorder_picking.state, "assigned")
        self.dbsource.whs_insert_read_and_synchronize_list()
        result_liste = self._select_wms_liste(back_whs_list)
        self.assertFalse(result_liste[0])
        # simulate WMS work set done to rest of backorder
        self.simulate_wms_cron({x: 2 for x in back_whs_list})
        result_liste = self._select_wms_liste(back_whs_list)
        self.assertEqual(str(result_liste[0]), "[(Decimal('2.000'), Decimal('2.000'))]")
        self.dbsource.whs_insert_read_and_synchronize_list()
        backorder_picking.button_validate()
        self.assertEqual(backorder_picking.state, "done")

    def _test_03_partial_picking_from_sale(self):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()
        self._clean_all()
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
        self.assertEqual(order1.state, "sale")
        # self.assertEqual(order1.mapped('picking_ids.state'), ['assigned'])
        if self.step_delivery == "one":
            self.assertEqual(len(order1.picking_ids), 1)
            picking = order1.picking_ids[0]
        else:
            self.assertEqual(len(order1.picking_ids), 2)
            picking = order1.picking_ids.filtered(
                lambda x: x.picking_type_id == self.warehouse.pick_type_id
            )
        self.assertEqual(len(picking.mapped("move_lines.whs_list_ids")), 4)

        # check WMS list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self._execute_select_all_valid_host_liste()
        self.assertEqual(len(whs_records), 4)
        # simulate WMS work: validate first move totally and second move partially
        whs_lists = picking.mapped("move_lines.whs_list_ids")
        self.simulate_wms_cron(
            {x: 0 if x.product_id == self.product3 else 5 for x in whs_lists}
        )
        for whs_list in whs_lists:
            result_liste = self._select_wms_liste(whs_list)
            self.assertEqual(
                str(result_liste[0]),
                "[(Decimal('5.000'), Decimal('5.000'))]"
                if whs_list.product_id == self.product1
                else "[(Decimal('10.000'), Decimal('5.000'))]"
                if whs_list.product_id == self.product2
                else "[(Decimal('20.000'), Decimal('0.000'))]"
                if whs_list.product_id == self.product3
                else "[(Decimal('20.000'), Decimal('5.000'))]",
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
            self.env[res["res_model"]].with_context(**res["context"])
        ).save()
        # User must set correctly quantity as set by WMS user, ignoring qty set
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
        if self.step_delivery == "one":
            self.assertEqual(len(order1.picking_ids), 2)
            backorder_picking = order1.picking_ids - picking
        else:
            self.assertEqual(len(order1.picking_ids), 3)
            backorder_picking = (
                order1.picking_ids.filtered(
                    lambda x: x.picking_type_id == self.warehouse.pick_type_id
                )
                - picking
            )
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
        # simulate WMS work: total process
        self.simulate_wms_cron({x: x.qta for x in whs_lists})

        self.dbsource.whs_insert_read_and_synchronize_list()
        # check WMS list for backorder is not created as the first is completed entirely
        # FIXME: what does the note above mean?
        res = self._execute_select_all_valid_host_liste()
        self.assertEqual(len(res), 3)
        backorder_picking.action_assign()

    def _test_04_unlink_sale_order(self):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()
        self._clean_all()
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
        if self.step_delivery == "one":
            self.assertEqual(len(order1.picking_ids), 1)
            picking = order1.picking_ids
        else:
            self.assertEqual(len(order1.picking_ids), 2)
            picking = order1.picking_ids.filtered(
                lambda x: x.picking_type_id == self.warehouse.pick_type_id
            )
        picking.action_assign()
        self.assertEqual(picking.state, "assigned")
        self.assertEqual(len(picking.mapped("move_lines.whs_list_ids")), 2)

        # check WMS list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            2,
        )
        # controlla che le liste WMS siano annullate (impostate con Qta=0)
        order1.action_cancel()
        # insert lists in WMS: this has to be invoked before every sql call!
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            0,
        )
        self.assertFalse(order1.mapped("picking_ids.move_lines.whs_list_ids"))
        order1.action_draft()
        order1.action_confirm()
        if self.step_delivery == "one":
            self.assertEqual(len(order1.picking_ids), 2)
            picking = order1.picking_ids.filtered(lambda x: x.state != "cancel")
        else:
            self.assertEqual(len(order1.picking_ids), 4)
            picking = order1.picking_ids.filtered(
                lambda x: x.picking_type_id == self.warehouse.pick_type_id
                and x.state != "cancel"
            )
        self.assertEqual(picking.mapped("move_lines.whs_list_ids.stato"), ["1", "1"])
        # insert lists in WMS: this has to be invoked before every sql call!
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            2,
        )
        # self.run_stock_procurement_scheduler()
        picking.action_assign()
        if self.step_delivery == "one":
            self.assertEqual(picking.state, "assigned")
        whs_lists = picking.mapped("move_lines.whs_list_ids")
        # todo it's not possibile to simulate a work in progress from WMS user, as there
        #  are only done lists in EXP_ORDINI* tables afaik (check it)
        self.simulate_wms_cron({x: x.qta for x in whs_lists})
        # check an order done cannot be cancelled, even if it is not already synced by
        # Odoo cron
        with self.assertRaises(UserError):
            order1.action_cancel()
        # Check product added to sale order after confirmation create new WMS lists
        # adding product to an existing open picking
        order_form2 = Form(order1)
        with order_form2.order_line.new() as order_line:
            order_line.product_id = self.product4
            order_line.product_uom_qty = 5
            order_line.price_unit = 100
        order1 = order_form2.save()
        pickings = order1.picking_ids.filtered(lambda x: x.state != "cancel")
        if self.step_delivery == "one":
            self.assertEqual(len(pickings), 1)
            picking = order1.picking_ids
        else:
            self.assertEqual(len(pickings), 2)
            picking = pickings.filtered(
                lambda x: x.picking_type_id == self.warehouse.pick_type_id
            )
        # get only the picking moved in WMS, which is in the "two steps option" only the
        # one moved from stock to output location
        # location_usage = "customer" if self.step_delivery == "one" else "internal"
        # pickings = order1.picking_ids.filtered(
        #     lambda x: x.state != "cancel"
        #     and x.location_dest_id.usage == location_usage)
        picking.action_assign()
        new_product_move_line_ids = picking.mapped("move_lines").filtered(
            lambda x: x.product_id == self.product4
        )
        self.assertTrue(new_product_move_line_ids.mapped("whs_list_ids"))
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            1,
        )

        # test changing qty of sale order line does not change the linked whs list
        order_line = order1.order_line[0]
        whs_lists = order_line.move_ids.filtered(lambda x: x.state != "cancel").mapped(
            "whs_list_ids"
        )
        if whs_lists:
            self.assertEqual(len(whs_lists), 1)
            whs_list = whs_lists[0]
            self.assertEqual(whs_list.qta, order_line.product_uom_qty)
        # initial_qty = order_line.product_uom_qty
        with self.assertRaises(UserError):
            # changing qty is forbidden
            # (todo in v. 12.0 wasn't forbidden in one step option, why?)
            order_line.write({"product_uom_qty": order_line.product_uom_qty + 6})
        # this part was in v. 12.0, now the change is no more accepted
        # new_whs_lists = order_line.move_ids.filtered(
        #     lambda x: x.state != "cancel"
        # ).mapped("whs_list_ids")
        # if new_whs_lists:
        #     new_whs_list = new_whs_lists - whs_lists
        #     self.assertEqual(whs_lists.qta, initial_qty)
        #     self.assertEqual(new_whs_list.qta, 6)

    def _test_06_purchase(self):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()
        self._clean_all()
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
        # check WMS list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            2,
        )
        # get available qty for product2 before purchase order
        qty_available_product2 = self.product2.qty_available
        # simulate WMS work: partial processing of product #2
        # and total of product #3
        whs_lists = purchase.mapped("picking_ids.move_lines.whs_list_ids")
        self.simulate_wms_cron(
            {x: 2 if x.product_id == self.product2 else 3 for x in whs_lists}
        )
        # check whs_list are elaborated
        for whs_list in whs_lists:
            result_liste = self._select_wms_liste(whs_list)
            self.assertEqual(whs_list.ragsoc, purchase.partner_id.name)
            self.assertEqual(
                str(result_liste[0]),
                "[(Decimal('17.000'), Decimal('2.000'))]"
                if whs_list.product_id == self.product2
                else "[(Decimal('3.000'), Decimal('3.000'))]",
            )

        # this update Odoo from WHS
        self.dbsource.whs_insert_read_and_synchronize_list()
        # sync inventory to test this product is not considered even if the user
        # hasn't completed the picking
        # WHSystem already has the 2 pc income from purchase order, so we add them
        # self.simulate_whs_cron_inventory(
        # self.product2, self.product2.qty_available + 2)
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
        wiz = Form(self.env[res["res_model"]].with_context(**res["context"])).save()
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
        result_liste = self._select_wms_liste(back_whs_list, "IMP")
        self.assertEqual(str(result_liste[0]), "[(Decimal('15.000'),)]")
        # TODO check cancel workflow without action_assign that create WMS list anyway
        self._check_cancel_workflow(backorder_picking, 1)
        backorder_picking.action_assign()
        # DO NOT simulate WMS work set done to rest of backorder
        # self.simulate_wms_cron({x: 18 for x in back_whs_list})
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
        # pickings linked to purchase order change state to "assigned" when a product is
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
            4,
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
        result_liste = self._select_wms_liste(po_whs_list, db_type="IMP")
        # WMS list is created for the increased qty
        self.assertEqual(str(result_liste[0]), "[(Decimal('7.000'),)]")

    def _mrp_partial_from_sale(self):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()
        self._clean_all()
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
        # Check whs list are added
        # In one step option 3 components and 1 finished product
        # In two steps option the move from stock to pre-production is done outside the
        # manufacturing process, as it is a normal stock picking
        self.dbsource.whs_insert_read_and_synchronize_list()
        created_whs_list_number = 4 if self.step_delivery == "one" else 3
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            created_whs_list_number,
        )

        # simulate whs work: consume 25% of components to produce 5 finished product
        # consumed and finished product are sent to WMS for the consumed/produced qty
        component_whs_lists = man_order.mapped("move_raw_ids.whs_list_ids")
        finished_whs_lists = man_order.mapped("move_finished_ids.whs_list_ids")
        self.simulate_wms_cron({x: x.qta * 0.25 for x in component_whs_lists})
        self.simulate_wms_cron({x: 5 for x in finished_whs_lists})

        for whs_list in component_whs_lists | finished_whs_lists:
            result_liste = self._select_wms_liste(whs_list)
            if whs_list.product_id == self.subproduct_1_1:
                self.assertIn(
                    str(result_liste[0]),
                    [
                        "[(Decimal('200.000'), Decimal('50.000'))]",
                        "[(Decimal('120.000'), Decimal('30.000'))]",
                    ],
                )
            elif whs_list.product_id == self.subproduct_2_1:
                self.assertEqual(
                    str(result_liste[0]), "[(Decimal('160.000'), Decimal('40.000'))]"
                )
            elif whs_list.product_id == self.top_product:
                self.assertEqual(
                    str(result_liste[0]), "[(Decimal('20.000'), Decimal('5.000'))]"
                )

        # this update Odoo from WMS
        self.dbsource.whs_insert_read_and_synchronize_list()
        action = man_order.with_context(test_connector_whs=True).button_mark_done()
        backorder_form = Form(
            self.env["mrp.production.backorder"].with_context(**action["context"])
        )
        backorder_form.save().action_backorder()
        self.assertEqual(
            len(man_order.procurement_group_id.mrp_production_ids),
            2 if self.step_delivery == "one" else 1,
        )
        if self.step_delivery == "one":
            self.assertEqual(man_order.state, "done")

        mo_backorder = man_order.procurement_group_id.mrp_production_ids[-1]
        if self.step_delivery == "one":
            self.assertEqual(mo_backorder.state, "confirmed")
            with self.assertRaises(UserError):
                # check production order cannot be done without WMS lists
                mo_backorder.with_context(test_connector_whs=True).button_mark_done()
        else:
            self.assertEqual(mo_backorder.state, "progress")

    def _mrp_total_from_sale(self):
        with self.assertRaises(ValidationError):
            self.dbsource.connection_test()
        self._clean_all()
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.env.ref("base.res_partner_12")
        order_form.date_order = fields.Datetime.now()
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
        man_order.button_plan()
        self.assertEqual(man_order.state, "confirmed")
        man_order.qty_producing = 20
        self._auto_fill_consumed_qty(man_order.move_raw_ids)
        self.assertTrue(man_order.mapped("move_raw_ids.move_line_ids"))
        # self.assertTrue(man_order.move_finished_ids.move_line_ids)
        # self.assertEqual(
        #     man_order.move_finished_ids.move_line_ids.mapped("state"), ["confirmed"]
        # )
        man_order.button_send_to_whs()
        self.assertTrue(man_order.sent_to_whs)
        # Check whs list are added
        # In one step option 3 components and 1 finished product
        # In two steps option the move from stock to pre-production is done outside the
        # manufacturing process, as it is a normal stock picking
        self.dbsource.whs_insert_read_and_synchronize_list()
        created_whs_list_number = 4 if self.step_delivery == "one" else 3
        self.assertEqual(
            len(self._execute_select_all_valid_host_liste()),
            created_whs_list_number,
        )

        # simulate whs work: consume 100% of components to produce 20 finished products
        component_whs_lists = man_order.mapped("move_raw_ids.whs_list_ids")
        finished_whs_lists = man_order.mapped("move_finished_ids.whs_list_ids")
        self.simulate_wms_cron(
            {x: x.qta for x in component_whs_lists | finished_whs_lists}
        )

        for whs_list in component_whs_lists | finished_whs_lists:
            result_liste = self._select_wms_liste(whs_list)
            if whs_list.product_id == self.subproduct_1_1:
                self.assertIn(
                    str(result_liste[0]),
                    [
                        "[(Decimal('200.000'), Decimal('200.000'))]",
                        "[(Decimal('120.000'), Decimal('120.000'))]",
                    ],
                )
            elif whs_list.product_id == self.subproduct_2_1:
                self.assertEqual(
                    str(result_liste[0]), "[(Decimal('160.000'), Decimal('160.000'))]"
                )
            elif whs_list.product_id == self.top_product:
                self.assertEqual(
                    str(result_liste[0]), "[(Decimal('20.000'), Decimal('20.000'))]"
                )

        # this update Odoo from WMS
        self.dbsource.whs_insert_read_and_synchronize_list()

        man_order.with_context(test_connector_whs=True).button_mark_done()
        self.assertEqual(man_order.state, "done")

    def test_00_complete_picking_from_sale_1step(self):
        self._configure_1_step_delivery()
        self._test_00_complete_picking_from_sale()

    def test_00a_complete_picking_from_sale_2steps(self):
        self._configure_2_steps_delivery()
        self._test_00_complete_picking_from_sale()

    def test_01_partial_picking_from_sale_1step(self):
        self._configure_1_step_delivery()
        self._test_01_partial_picking_from_sale()

    def test_01a_partial_picking_from_sale_2steps(self):
        self._configure_2_steps_delivery()
        self._test_01_partial_picking_from_sale()

    def test_02_partial_picking_partial_available_from_sale_1step(self):
        self._configure_1_step_delivery()
        self._test_02_partial_picking_partial_available_from_sale()

    def test_02a_partial_picking_partial_available_from_sale_2steps(self):
        self._configure_2_steps_delivery()
        self._test_02_partial_picking_partial_available_from_sale()

    def test_03_partial_picking_from_sale_1step(self):
        self._configure_1_step_delivery()
        self._test_03_partial_picking_from_sale()

    def test_03a_partial_picking_from_sale_2steps(self):
        self._configure_2_steps_delivery()
        self._test_03_partial_picking_from_sale()

    def test_04_unlink_sale_order_1step(self):
        self._configure_1_step_delivery()
        self._test_04_unlink_sale_order()

    def test_04a_unlink_sale_order_2steps(self):
        self._configure_2_steps_delivery()
        self._test_04_unlink_sale_order()

    def test_06_purchase_1step(self):
        self._configure_1_step_delivery()
        self._test_06_purchase()

    def test_06a_purchase_2steps(self):
        self._configure_2_steps_delivery()
        self._test_06_purchase()

    def test_08_mrp_partial_from_sale_1step(self):
        self._configure_1_step_delivery()
        self._mrp_partial_from_sale()

    def test_08a_mrp_partial_from_sale_2steps(self):
        self._configure_2_steps_delivery()
        self._mrp_partial_from_sale()

    def test_09_mrp_total_from_sale_1step(self):
        self._configure_1_step_delivery()
        self._mrp_total_from_sale()

    def test_09a_mrp_total_from_sale_2steps(self):
        self._configure_2_steps_delivery()
        self._mrp_total_from_sale()
