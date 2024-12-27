from odoo.addons.base_external_dbsource.exceptions import ConnectionSuccessError
from odoo.tests import tagged
from odoo.tests.common import Form
from odoo.addons.connector_wms_whs.tests.test_connector_wms_whs import TestConnectorWmsWhs
from sqlalchemy import text as sql_text


@tagged("-standard", "test_wms")
class TestConnectorWmsModula(TestConnectorWmsWhs):
    def setUp(self):
        super().setUp()

    def test_05_repair(self):
        with self.assertRaises(ConnectionSuccessError):
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
            len(
                self.dbsource.execute_mssql(
                    sqlquery=sql_text(
                        "SELECT * FROM HOST_LISTE WHERE Elaborato!=:Elaborato AND "
                        "Qta!=:Qta"),
                    sqlparams=dict(Elaborato=5, Qta=0),
                    metadata=None,
                )[0]
            ),
            whs_len_records + 2,
        )

        # simulate whs work: partial processing of product #2
        # and total of product #3
        whs_lists = repair.mapped('operations.move_id.whs_list_ids')
        for whs_list in whs_lists:
            set_liste_elaborated_query = \
                "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s WHERE " \
                "NumLista = '%s' AND NumRiga = '%s'" % (
                    2 if whs_list.product_id == self.product2 else 3,
                    whs_list.num_lista, whs_list.riga
                )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=sql_text(set_liste_elaborated_query),
                sqlparams=None,
                metadata=None,
            )

        for whs_list in whs_lists:
            whs_select_query = \
                "SELECT Qta, QtaMovimentata FROM HOST_LISTE WHERE Elaborato = 4 AND " \
                "NumLista = '%s' AND NumRiga = '%s'" % (
                    whs_list.num_lista, whs_list.riga
                )
            result_liste = self.dbsource.execute_mssql(
                sqlquery=sql_text(whs_select_query), sqlparams=None, metadata=None
            )
            self.assertEqual(
                str(result_liste[0]),
                "[(Decimal('5.000'), Decimal('2.000'))]"
                if whs_list.product_id == self.product2 else
                "[(Decimal('3.000'), Decimal('3.000'))]")

        # this update Odoo from WHS
        self.dbsource.whs_insert_read_and_synchronize_list()
        # check whs_list are elaborated
        for whs_list in whs_lists:
            whs_select_query = \
                "SELECT Qta, QtaMovimentata FROM HOST_LISTE WHERE Elaborato = 5 AND " \
                "NumLista = '%s' AND NumRiga = '%s'" % (
                    whs_list.num_lista, whs_list.riga
                )
            result_liste = self.dbsource.execute_mssql(
                sqlquery=sql_text(whs_select_query), sqlparams=None, metadata=None
            )
            self.assertIn(
                "[(Decimal('5.000'), Decimal('2.000'))]"
                if whs_list.product_id == self.product2 else
                "[(Decimal('3.000'), Decimal('3.000'))]",
                str(result_liste))
