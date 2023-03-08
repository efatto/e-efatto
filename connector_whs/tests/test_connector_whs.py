# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.addons.base_external_dbsource.exceptions import ConnectionSuccessError
from odoo.tests import tagged
from odoo.tools import mute_logger, relativedelta
from odoo.exceptions import UserError
import os
import time


@tagged('post_install', '-at_install')
class TestConnectorWhs(TransactionCase):

    def _create_sale_order_line(self, order, product, qty, priority='0'):
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': product.id,
            'product_uom_qty': qty,
            'price_unit': 100,
            'priority': priority,
            })
        line.product_id_change()
        line._convert_to_write(line._cache)
        return line

    def setUp(self):
        super(TestConnectorWhs, self).setUp()
        dbsource_model = self.env['base.external.dbsource']
        dbsource = dbsource_model.search([
            ('name', '=', 'Odoo WHS local server')
        ])
        if not dbsource:
            conn_file = os.path.join(os.path.expanduser('~'), 'connection_string.txt')
            if not os.path.isfile(conn_file):
                raise UserError("Missing connection string!")
            with open(conn_file, 'r') as file:
                conn_string = file.read().replace('\n', '')
            dbsource = dbsource_model.create({
                'name': 'Odoo WHS local server',
                'conn_string_sandbox': conn_string,
                'connector': 'mssql',
                'location_id': self.env.ref('stock.stock_location_stock').id,
            })
        self.dbsource = dbsource
        self.src_location = self.env.ref('stock.stock_location_stock')
        self.dest_location = self.env.ref('stock.stock_location_customers')
        self.procurement_model = self.env['procurement.group']
        self.partner = self.env.ref('base.res_partner_2')
        # Create product with 16 on hand
        self.product1 = self.env['product.product'].create([{
            'name': 'test product1',
            'default_code': 'PRODUCT1',
            'type': 'product',
        }])
        self.StockQuant = self.env['stock.quant']
        self.quant_product1 = self.StockQuant.create([{
            'product_id': self.product1.id,
            'location_id': self.src_location.id,
            'quantity': 16.0,
        }])
        # Create product with 8 on hand
        self.product2 = self.env['product.product'].create([{
            'name': 'test product2',
            'default_code': 'PRODUCT2',
            'type': 'product',
        }])
        self.quant_product2 = self.StockQuant.create([{
            'product_id': self.product2.id,
            'location_id': self.src_location.id,
            'quantity': 8.0,
        }])
        # Large Cabinet, 250 on hand
        self.product3 = self.env.ref('product.product_product_6')
        # Drawer Black, 0 on hand
        self.product4 = self.env.ref('product.product_product_16')
        self.product5 = self.env.ref('product.product_product_20')
        self.product1.invoice_policy = 'order'
        self.product1.write({
            'customer_ids': [
                (0, 0, {
                    'name': self.partner.id,
                    'product_code': 'CUSTOMERCODE',
                    'product_name': 'Product customer name',
                })
            ]
        })
        self.product2.invoice_policy = 'order'

    def run_stock_procurement_scheduler(self):
        with mute_logger('odoo.addons.stock.models.procurement'):
            self.procurement_model.run_scheduler(True)
            time.sleep(60)

    def simulate_whs_cron(self, whs_lists, elaborato):
        for whs_list in whs_lists:
            set_liste_elaborated_query = \
                "UPDATE HOST_LISTE SET Elaborato=%s, QtaMovimentata=%s WHERE " \
                "NumLista = '%s' AND NumRiga = '%s'" % (
                    elaborato,
                    whs_list.qta,
                    whs_list.num_lista,
                    whs_list.riga
                )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=set_liste_elaborated_query, sqlparams=None, metadata=None)

    def check_cancel_workflow(self, picking, list_len):
        whs_records = self.dbsource.execute_mssql(
            sqlquery="SELECT Elaborato, NumLista, NumRiga, * FROM HOST_LISTE "
                     "WHERE Riferimento = '%s'" % (
                         picking.sale_id.name if picking.sale_id
                         else picking.purchase_id.name
                     ),
            sqlparams=None, metadata=None)[0]
        whs_lists = picking.mapped('move_lines.whs_list_ids')
        self.assertEqual(len(whs_lists), list_len)
        whs_list = whs_lists[0]
        self.assertEqual(whs_list.stato, '2')
        self.run_stock_procurement_scheduler()
        if all(x.state == 'assigned' for x in picking.move_lines):
            self.assertEqual(picking.state, 'assigned')
        else:
            self.assertEqual(picking.state, 'waiting')
        picking.action_cancel()
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(picking.state, 'cancel')
        # check whs lists are in stato '3' -> 'Da NON elaborare'
        self.assertEqual(set(picking.move_lines.mapped('whs_list_ids.stato')), {'3'})
        self.simulate_whs_cron(picking.move_lines.mapped('whs_list_ids'), 5)
        whs_records1 = self.dbsource.execute_mssql(
            sqlquery="SELECT Elaborato, NumLista, NumRiga, * FROM HOST_LISTE "
                     "WHERE Riferimento = '%s'" % (
                         picking.sale_id.name if picking.sale_id
                         else picking.purchase_id.name
                     ),
            sqlparams=None, metadata=None)[0]
        self.assertEqual(len(whs_records1), len(whs_records))
        self.assertEqual(set([x[0] for x in whs_records1]), {5})
        # restore picking to assigned state
        picking.action_back_to_draft()
        picking.action_confirm()
        if picking.sale_id:
            picking.action_assign()
        whs_lists = picking.mapped('move_lines.whs_list_ids').filtered(
            lambda x: x.stato != '3'
        )
        self.assertEqual(len(whs_lists), list_len)
        whs_list = whs_lists[0]
        self.assertTrue(whs_list)
        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records2 = self.dbsource.execute_mssql(
            sqlquery="SELECT Elaborato, NumLista, NumRiga, * FROM HOST_LISTE "
                     "WHERE Riferimento = '%s'" % (
                         picking.sale_id.name if picking.sale_id
                         else picking.purchase_id.name
                     ),
            sqlparams=None, metadata=None)[0]
        self.assertEqual(len(whs_records2), len(whs_records) + list_len)
        for Elaborato in set([x[0] for x in whs_records2]):
            # WHS cron change Elaborato to 2 in an un-controllable time
            self.assertIn(Elaborato, {5, 1, 2})
        return whs_list

    def test_00_complete_picking_from_sale(self):
        with self.assertRaises(ConnectionSuccessError):
            self.dbsource.connection_test()
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery='DELETE FROM HOST_LISTE', sqlparams=None, metadata=None)
        whs_len_records = len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0])
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'client_order_ref': 'Rif. SO customer',
            })
        self._create_sale_order_line(order1, self.product1, 5)
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
        whs_records = self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0]
        self.assertEqual(len(whs_records), whs_len_records + 1)
        for whs_record in whs_records:
            self.assertTrue(order1.client_order_ref in whs_record.values())
            if self.product1.default_code in whs_record.values():
                self.assertTrue(self.product1.customer_ids[0].product_code in
                                whs_record.values())
            else:
                self.assertFalse(self.product1.customer_ids[0].product_code in
                                 whs_record.values())
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
        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0]
        self.assertEqual(len(whs_records), whs_len_records + 2)
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
            sqlquery=set_liste_elaborated_query, sqlparams=None, metadata=None)

        whs_select_query = \
            "SELECT Qta, QtaMovimentata, Lotto, Lotto3, Lotto3, Lotto4, Lotto5 " \
            "FROM HOST_LISTE WHERE Elaborato = 4 AND " \
            "NumLista = '%s' AND NumRiga = '%s'" % (
                whs_list.num_lista, whs_list.riga
            )
        result_liste = self.dbsource.execute_mssql(
            sqlquery=whs_select_query, sqlparams=None, metadata=None)
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

    def test_01_partial_picking_from_sale(self):
        with self.assertRaises(ConnectionSuccessError):
            self.dbsource.connection_test()
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery='DELETE FROM HOST_LISTE', sqlparams=None, metadata=None)
        whs_len_records = len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0])
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'client_order_ref': 'Rif. SO customer',
            })
        self._create_sale_order_line(order1, self.product1, 5, "2")
        self._create_sale_order_line(order1, self.product1, 5)
        order1.action_confirm()
        self.assertEqual(order1.state, 'sale')
        self.assertEqual(order1.priority, '2')
        for picking in order1.picking_ids:
            if all(x.state == 'assigned' for x in picking.move_lines):
                self.assertEqual(picking.state, 'assigned')
            else:
                self.assertEqual(picking.state, 'waiting')
        picking = order1.picking_ids[0]
        self.assertEqual(len(picking.mapped('move_lines.whs_list_ids')), 2)

        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self.dbsource.execute_mssql(
            sqlquery="SELECT Elaborato, NumLista, NumRiga, * FROM HOST_LISTE",
            sqlparams=None, metadata=None)[0]
        self.assertEqual(len(whs_records), whs_len_records + 2)
        self.assertEqual(set([x[0] for x in whs_records]), {1})
        self.assertEqual(set(
            [x.stato for x in picking.mapped('move_lines.whs_list_ids')]), {'2'})
        for whs_record in whs_records:
            self.assertTrue(order1.client_order_ref in whs_record.values())
            if self.product1.default_code in whs_record.values():
                self.assertTrue(self.product1.customer_ids[0].product_code in
                                whs_record.values())
            else:
                self.assertFalse(self.product1.customer_ids[0].product_code in
                                 whs_record.values())

        whs_list = self.check_cancel_workflow(picking, 2)

        whs_records = self.dbsource.execute_mssql(
            sqlquery="SELECT Elaborato, NumLista, NumRiga, * FROM HOST_LISTE",
            sqlparams=None, metadata=None)[0]
        self.assertEqual(len(whs_records), whs_len_records + 4)
        # simulate whs work: validate first move partially (3 over 5)
        set_liste_elaborated_query = \
            "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s WHERE " \
            "NumLista = '%s' AND NumRiga = '%s'" % (
                3, whs_list.num_lista, whs_list.riga
            )
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=set_liste_elaborated_query, sqlparams=None, metadata=None)

        whs_select_query = \
            "SELECT Qta, QtaMovimentata, Priorita FROM HOST_LISTE WHERE Elaborato = 4 "\
            "AND NumLista = '%s' AND NumRiga = '%s'" % (
                whs_list.num_lista, whs_list.riga
            )
        result_liste = self.dbsource.execute_mssql(
            sqlquery=whs_select_query, sqlparams=None, metadata=None)
        self.assertIn("[(Decimal('5.000'), Decimal('3.000'), 1)]", str(result_liste))

        self.dbsource.whs_insert_read_and_synchronize_list()

        # check move and picking linked to sale order have changed state to done
        self.assertEqual(set(picking.move_lines.mapped('state')), {'assigned'})
        if all(x.state == 'assigned' for x in picking.move_lines):
            self.assertEqual(picking.state, 'assigned')
        else:
            self.assertEqual(picking.state, 'waiting')
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
        whs_lists = backorder_picking.mapped('move_lines.whs_list_ids').filtered(
            lambda x: x.stato != '3'
        )
        for whs_list in whs_lists:
            # simulate whs work: total process
            set_liste_elaborated_query = \
                "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s WHERE " \
                "NumLista = '%s' AND NumRiga = '%s'" % (
                    whs_list.qta,
                    whs_list.num_lista, whs_list.riga
                )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=set_liste_elaborated_query, sqlparams=None, metadata=None)

        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0]),
            whs_len_records + 4)

        # check back picking is waiting for whs process
        self.assertEqual(len(order1.picking_ids), 2)
        self.assertEqual(backorder_picking.state, 'assigned')
        self.assertEqual(backorder_picking.move_lines[0].state, 'assigned')

    def test_02_partial_picking_partial_available_from_sale(self):
        with self.assertRaises(ConnectionSuccessError):
            self.dbsource.connection_test()
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery='DELETE FROM HOST_LISTE', sqlparams=None, metadata=None)
        whs_len_records = len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0])
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'client_order_ref': 'Rif. SO customer',
            })
        self._create_sale_order_line(order1, self.product1, 5, "3")
        self._create_sale_order_line(order1, self.product2, 20)
        order1.action_confirm()
        self.assertEqual(order1.state, 'sale')
        self.assertEqual(order1.priority, '3')
        picking = order1.picking_ids[0]
        self.assertEqual(len(picking.mapped('move_lines.whs_list_ids')), 2)
        self.assertEqual(picking.state, 'assigned')

        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE WHERE Elaborato != 5",
            sqlparams=None, metadata=None)[0]
        self.assertEqual(len(whs_records), whs_len_records + 2)
        for whs_record in whs_records:
            self.assertTrue(order1.client_order_ref in whs_record.values())
            if self.product1.default_code in whs_record.values():
                self.assertTrue(self.product1.customer_ids[0].product_code in
                                whs_record.values())
            else:
                self.assertFalse(self.product1.customer_ids[0].product_code in
                                 whs_record.values())

        whs_lists = picking.mapped('move_lines.whs_list_ids')
        for whs_list in whs_lists:
            # simulate whs work: partial processing of product #1
            # and total of product #2 so it is -4 on warehouse
            set_liste_elaborated_query = \
                "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s WHERE " \
                "NumLista = '%s' AND NumRiga = '%s'" % (
                    whs_list.qta - (2 if whs_list.product_id == self.product1 else 0),
                    whs_list.num_lista, whs_list.riga
                )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=set_liste_elaborated_query, sqlparams=None, metadata=None)

        for whs_list in whs_lists:
            whs_select_query = \
                "SELECT Qta, QtaMovimentata, Priorita FROM HOST_LISTE WHERE Elaborato "\
                "= 4 AND NumLista = '%s' AND NumRiga = '%s'" % (
                    whs_list.num_lista, whs_list.riga
                )
            result_liste = self.dbsource.execute_mssql(
                sqlquery=whs_select_query, sqlparams=None, metadata=None)
            self.assertEqual(
                str(result_liste[0]),
                "[(Decimal('5.000'), Decimal('3.000'), 2)]"
                if whs_list.product_id == self.product1 else
                "[(Decimal('20.000'), Decimal('20.000'), 2)]")

        self.dbsource.whs_insert_read_and_synchronize_list()

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
        for whs_list in whs_lists:
            # simulate whs work: total process
            set_liste_elaborated_query = \
                "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s WHERE " \
                "NumLista = '%s' AND NumRiga = '%s'" % (
                    2 if whs_list.product_id == self.product2 else 3,
                    whs_list.num_lista, whs_list.riga
                )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=set_liste_elaborated_query, sqlparams=None, metadata=None)

        # this function do the action_assign() too
        self.dbsource.whs_insert_read_and_synchronize_list()
        # picking.action_pack_operation_auto_fill()
        backorder_wiz.process()
        self.assertEqual(picking.state, 'done')

        # check back picking is waiting as Odoo qty is not considered
        self.assertEqual(len(order1.picking_ids), 2)
        backorder_picking = order1.picking_ids - picking
        self.assertEqual(backorder_picking.move_lines.mapped('state'), ['assigned'])
        # todo check also a 'partially_available'
        self.assertEqual(backorder_picking.state, 'assigned')

        # todo check whs_list for backorder is created
        self.dbsource.whs_insert_read_and_synchronize_list()
        back_whs_list = backorder_picking.mapped('move_lines.whs_list_ids')
        whs_select_query = \
            "SELECT Qta, QtaMovimentata FROM HOST_LISTE WHERE " \
            "NumLista = '%s' AND NumRiga = '%s'" % (
                back_whs_list.num_lista, back_whs_list.riga
            )
        result_liste = self.dbsource.execute_mssql(
            sqlquery=whs_select_query, sqlparams=None, metadata=None)
        self.assertEqual(str(result_liste[0]), "[(Decimal('2.000'), None)]")

        # simulate whs work set done to rest of backorder
        set_liste_elaborated_query = \
            "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s WHERE " \
            "NumLista = '%s' AND NumRiga = '%s'" % (
                2, back_whs_list.num_lista, back_whs_list.riga
            )
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=set_liste_elaborated_query, sqlparams=None, metadata=None)

        self.dbsource.whs_insert_read_and_synchronize_list()
        backorder_picking.button_validate()
        self.assertEqual(backorder_picking.state, 'done')

    def test_03_partial_picking_from_sale(self):
        with self.assertRaises(ConnectionSuccessError):
            self.dbsource.connection_test()
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery='DELETE FROM HOST_LISTE', sqlparams=None, metadata=None)
        whs_len_records = len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0])
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'client_order_ref': 'Rif. SO customer',
            })
        self._create_sale_order_line(order1, self.product1, 5)  # 16
        self._create_sale_order_line(order1, self.product2, 10)  # 8
        self._create_sale_order_line(order1, self.product3, 20, "1")  # 250
        self._create_sale_order_line(order1, self.product4, 20)  # 0
        order1.action_confirm()
        self.assertEqual(order1.state, 'sale')
        self.assertEqual(order1.mapped('picking_ids.state'), ['assigned'])
        picking = order1.picking_ids[0]
        self.assertEqual(len(picking.mapped('move_lines.whs_list_ids')), 4)

        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0]
        self.assertEqual(len(whs_records), whs_len_records + 4)
        for whs_record in whs_records:
            self.assertTrue(order1.client_order_ref in whs_record.values())
            if self.product1.default_code in whs_record.values():
                self.assertTrue(self.product1.customer_ids[0].product_code in
                                whs_record.values())
            else:
                self.assertFalse(self.product1.customer_ids[0].product_code in
                                 whs_record.values())
        # simulate whs work: validate first move totally and second move partially
        whs_lists = picking.mapped('move_lines.whs_list_ids')
        for whs_list in whs_lists:
            # simulate whs work: total process
            set_liste_elaborated_query = \
                "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s WHERE " \
                "NumLista = '%s' AND NumRiga = '%s'" % (
                    0 if whs_list.product_id == self.product3 else 5,
                    whs_list.num_lista, whs_list.riga
                )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=set_liste_elaborated_query, sqlparams=None, metadata=None)

        for whs_l in whs_lists:
            whs_select_query = \
                "SELECT Qta, QtaMovimentata, Priorita FROM HOST_LISTE WHERE Elaborato" \
                " = 4 AND NumLista = '%s' AND NumRiga = '%s'" % (
                    whs_l.num_lista, whs_l.riga
                )
            result_liste = self.dbsource.execute_mssql(
                sqlquery=whs_select_query, sqlparams=None, metadata=None)
            self.assertEqual(
                str(result_liste[0]),
                "[(Decimal('5.000'), Decimal('5.000'), 0)]"
                if whs_l.product_id == self.product1 else
                "[(Decimal('10.000'), Decimal('5.000'), 0)]"
                if whs_l.product_id == self.product2 else
                "[(Decimal('20.000'), Decimal('0.000'), 0)]"
                if whs_l.product_id == self.product3 else
                "[(Decimal('20.000'), Decimal('5.000'), 0)]")

        self.dbsource.whs_insert_read_and_synchronize_list()

        # check move and picking linked to sale order have changed state to done
        for move_line in picking.move_lines:
            self.assertEqual(
                move_line.state,
                'assigned' if move_line.product_id in [
                    self.product1, self.product3] else
                'confirmed' if move_line.product_id == self.product4
                else 'partially_available')
            for stock_move_line in move_line.move_line_ids:
                if stock_move_line.product_id in [
                        self.product1, self.product2, self.product4]:
                    self.assertAlmostEqual(stock_move_line.qty_done, 5.0)
                if stock_move_line.product_id == self.product3:
                    self.assertAlmostEqual(stock_move_line.qty_done, 0)
        self.run_stock_procurement_scheduler()
        # check that action_assign run by scheduler do not change state
        self.run_stock_procurement_scheduler()
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
        # check backorder whs list has the correct qty
        self.assertEqual(len(order1.picking_ids), 2)
        backorder_picking = order1.picking_ids - picking
        for move_line in backorder_picking.move_lines:
            self.assertAlmostEqual(move_line.whs_list_ids[0].qta, 5 if
                                   move_line.product_id == self.product2 else 20 if
                                   move_line.product_id == self.product3 else 15)

        # Simulate whs user validation
        whs_lists = picking.mapped('move_lines.whs_list_ids')
        for whs_list in whs_lists:
            # simulate whs work: total process
            set_liste_elaborated_query = \
                "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s WHERE " \
                "NumLista = '%s' AND NumRiga = '%s'" % (
                    whs_list.qta,
                    whs_list.num_lista, whs_list.riga
                )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=set_liste_elaborated_query, sqlparams=None, metadata=None)

        self.dbsource.whs_insert_read_and_synchronize_list()
        # picking.action_pack_operation_auto_fill()
        backorder_wiz.process()
        # check whs list for backorder is not created as the first is completed entirely
        self.dbsource.whs_insert_read_and_synchronize_list()
        res = self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0]
        self.assertEqual(len(res), whs_len_records + 6)
        self.run_stock_procurement_scheduler()
        backorder_picking.action_assign()
        # for move_line in backorder_picking.move_lines:
        #     self.assertEqual(
        #         move_line.state,
        #         'confirmed' if move_line.product_id == self.product2 else
        #         'partially_available' if move_line.product_id == self.product4 else
        #         'assigned')

    def test_04_unlink_sale_order(self):
        with self.assertRaises(ConnectionSuccessError):
            self.dbsource.connection_test()
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery='DELETE FROM HOST_LISTE', sqlparams=None, metadata=None)
        whs_len_records = len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0])
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'client_order_ref': 'Rif. SO customer',
            })
        self._create_sale_order_line(order1, self.product1, 5)
        self._create_sale_order_line(order1, self.product2, 5)
        order1.action_confirm()
        self.assertEqual(order1.state, 'sale')
        self.run_stock_procurement_scheduler()
        self.assertEqual(order1.mapped('picking_ids.state'), ['assigned'])
        picking = order1.picking_ids[0]
        self.assertEqual(len(picking.mapped('move_lines.whs_list_ids')), 2)

        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0]),
            whs_len_records + 2)
        # check whs non ci siano i relativi record
        order1.action_cancel()
        self.assertEqual(len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0]),
            whs_len_records + 2)
        self.assertEqual(
            set(order1.mapped('picking_ids.move_lines.whs_list_ids.stato')), {'3'})
        order1.action_draft()
        order1.action_confirm()
        self.assertEqual(len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0]),
            whs_len_records + 2)
        # insert lists in WHS
        self.dbsource.whs_insert_read_and_synchronize_list()
        # wait for WHS syncronization
        time.sleep(10)
        picking = order1.picking_ids.filtered(lambda x: x.state != 'cancel')
        self.run_stock_procurement_scheduler()
        if all(x.state == 'assigned' for x in picking.move_lines):
            self.assertEqual(picking.state, 'assigned')
        else:
            self.assertEqual(picking.state, 'cancel')
        hyddemo_whs_lists = picking.mapped('move_lines.whs_list_ids')
        lists = {x.riga: x.num_lista for x in hyddemo_whs_lists}
        # simulate launch from WHS user
        set_liste_elaborating_query = \
            "UPDATE HOST_LISTE SET Elaborato=3 WHERE " \
            " %s " % (
                " OR ".join(
                    "(NumLista = '%s' AND NumRiga = '%s')" % (
                        lists[y], y) for y in lists))
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=set_liste_elaborating_query, sqlparams=None, metadata=None)
        with self.assertRaises(UserError):
            order1.action_cancel()
        # Check product added to sale order after confirmation create new whs lists
        # adding product to an existing open picking
        whs_len_records = len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0])
        so_line = self._create_sale_order_line(order1, self.product4, 5)
        pickings = order1.picking_ids.filtered(lambda x: x.state == "assigned")
        pickings.action_assign()
        new_product_move_line_ids = order1.picking_ids.mapped('move_lines').filtered(
            lambda x: x.product_id == self.product4
        )
        self.assertTrue(new_product_move_line_ids.mapped("whs_list_ids"))
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0]),
            whs_len_records + 1)

        # test change qty of sale order line is forbidden
        with self.assertRaises(UserError):
            so_line.write({"product_uom_qty": 17})

    def _create_repair_order_line(self, repair, product, qty):
        line = self.env['repair.line'].create({
            'name': 'Add product',
            'repair_id': repair.id,
            'type': 'add',
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': product.uom_id.id,
            'price_unit': 5,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.location_production').id,
        })
        line.onchange_product_id()
        line._convert_to_write(line._cache)
        return line

    def test_05_repair(self):
        with self.assertRaises(ConnectionSuccessError):
            self.dbsource.connection_test()
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery='DELETE FROM HOST_LISTE', sqlparams=None, metadata=None)
        whs_len_records = len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0])
        repair = self.env['repair.order'].create({
            'product_id': self.product1.id,
            'product_uom': self.product1.uom_id.id,
            'partner_id': self.partner.id,
            'product_qty': 1,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            })
        self._create_repair_order_line(repair, self.product2, 5)
        self._create_repair_order_line(repair, self.product3, 3)
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
        self.assertEqual(len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE WHERE Elaborato != 5",
            sqlparams=None, metadata=None)[0]),
            whs_len_records + 2)

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
                sqlquery=set_liste_elaborated_query, sqlparams=None, metadata=None)

        for whs_list in whs_lists:
            whs_select_query = \
                "SELECT Qta, QtaMovimentata FROM HOST_LISTE WHERE Elaborato = 4 AND " \
                "NumLista = '%s' AND NumRiga = '%s'" % (
                    whs_list.num_lista, whs_list.riga
                )
            result_liste = self.dbsource.execute_mssql(
                sqlquery=whs_select_query, sqlparams=None, metadata=None)
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
                sqlquery=whs_select_query, sqlparams=None, metadata=None)
            self.assertIn(
                "[(Decimal('5.000'), Decimal('2.000'))]"
                if whs_list.product_id == self.product2 else
                "[(Decimal('3.000'), Decimal('3.000'))]",
                str(result_liste))

    def _create_purchase_order_line(self, order, product, qty, date_planned):
        line = self.env['purchase.order.line'].create({
            'order_id': order.id,
            'product_id': product.id,
            'product_uom': product.uom_po_id.id,
            'name': product.name,
            'product_qty': qty,
            'price_unit': 100,
            'date_planned': date_planned,
            })
        line.order_id.onchange_partner_id()
        return line

    def test_06_purchase(self):
        with self.assertRaises(ConnectionSuccessError):
            self.dbsource.connection_test()
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery='DELETE FROM HOST_LISTE', sqlparams=None, metadata=None)
        whs_len_records = len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0])
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            })
        self._create_purchase_order_line(
            purchase, self.product2, 20,
            fields.Datetime.today() + relativedelta(month=1))
        self._create_purchase_order_line(
            purchase, self.product3, 3,
            fields.Datetime.today() + relativedelta(month=1))
        purchase.button_approve()
        self.assertEqual(
            purchase.state, 'purchase', 'Purchase state should be "Purchase"')
        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0]),
            whs_len_records + 2)

        # simulate whs work: partial processing of product #2
        # and total of product #3
        whs_lists = purchase.mapped('picking_ids.move_lines.whs_list_ids')
        for whs_list in whs_lists:
            set_liste_elaborated_query = \
                "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s WHERE " \
                "NumLista = '%s' AND NumRiga = '%s'" % (
                    2 if whs_list.product_id == self.product2 else 3,
                    whs_list.num_lista, whs_list.riga
                )
            self.dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=set_liste_elaborated_query, sqlparams=None, metadata=None)

        for whs_list in whs_lists:
            whs_select_query = \
                "SELECT Qta, QtaMovimentata FROM HOST_LISTE WHERE Elaborato = 4 AND " \
                "NumLista = '%s' AND NumRiga = '%s'" % (
                    whs_list.num_lista, whs_list.riga
                )
            result_liste = self.dbsource.execute_mssql(
                sqlquery=whs_select_query, sqlparams=None, metadata=None)
            self.assertEqual(
                str(result_liste[0]),
                "[(Decimal('20.000'), Decimal('2.000'))]"
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
                sqlquery=whs_select_query, sqlparams=None, metadata=None)
            self.assertEqual(
                str(result_liste[0]),
                "[(Decimal('20.000'), Decimal('2.000'))]"
                if whs_list.product_id == self.product2 else
                "[(Decimal('3.000'), Decimal('3.000'))]")

        # simulate user partial validate of picking and check backorder exist
        picking = purchase.picking_ids[0]
        self.run_stock_procurement_scheduler()
        if all(x.state == 'assigned' for x in picking.move_lines):
            self.assertEqual(picking.state, 'assigned')
        else:
            self.assertEqual(picking.state, 'waiting')
        # check that action_assign run by scheduler do not change state
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        picking.action_pack_operation_auto_fill()
        backorder_wiz_id = picking.button_validate()['res_id']
        backorder_wiz = self.env['stock.backorder.confirmation'].browse(
            backorder_wiz_id)
        backorder_wiz.process()
        self.assertEqual(picking.state, 'done')

        # check back picking is waiting as waiting for WHS work
        self.assertEqual(len(purchase.picking_ids), 2)
        backorder_picking = purchase.picking_ids - picking
        self.run_stock_procurement_scheduler()
        for picking in purchase.picking_ids:
            if all(x.state == 'assigned' for x in picking.move_lines):
                self.assertEqual(picking.state, 'assigned')

        # check whs_list for backorder is created
        self.dbsource.whs_insert_read_and_synchronize_list()
        back_whs_list = backorder_picking.mapped('move_lines.whs_list_ids')
        whs_select_query = \
            "SELECT Qta, QtaMovimentata FROM HOST_LISTE WHERE " \
            "NumLista = '%s' AND NumRiga = '%s'" % (
                back_whs_list.num_lista, back_whs_list.riga
            )
        result_liste = self.dbsource.execute_mssql(
            sqlquery=whs_select_query, sqlparams=None, metadata=None)
        self.assertEqual(str(result_liste[0]), "[(Decimal('18.000'), None)]")
        # TODO check cancel workflow without action_assign that create whs list anyway
        self.check_cancel_workflow(backorder_picking, 1)
        backorder_picking.action_assign()
        # simulate whs work set done to rest of backorder
        set_liste_elaborated_query = \
            "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s WHERE " \
            "NumLista = '%s' AND NumRiga = '%s'" % (
                18, back_whs_list.num_lista, back_whs_list.riga
            )
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=set_liste_elaborated_query, sqlparams=None, metadata=None)

        self.dbsource.whs_insert_read_and_synchronize_list()
        backorder_picking.button_validate()
        self.assertEqual(backorder_picking.state, 'assigned')
        self.run_stock_procurement_scheduler()
        self.assertEqual(backorder_picking.state, 'assigned')
        self.assertFalse(all(whs_list.stato == '3' for whs_list in
                             backorder_picking.move_lines.whs_list_ids))
        # Check product added to purchase order after confirm create whs list with
        # different date_planned which create a new picking (as this module depends on
        # purchase_delivery_split_date)
        whs_len_records = len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0])
        self._create_purchase_order_line(
            purchase, self.product4, 20,
            fields.Datetime.today() + relativedelta(month=2))
        new_picking = purchase.picking_ids - (picking | backorder_picking)
        new_picking.action_assign()
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0]),
            whs_len_records + 1)
        # Check product added to purchase order after confirmation create new whs lists
        # adding product to an existing open picking
        self._create_purchase_order_line(
            purchase, self.product5, 20,
            fields.Datetime.today() + relativedelta(month=2))
        po_line = self._create_purchase_order_line(
            purchase, self.product5, 20,
            fields.Datetime.today() + relativedelta(month=2))
        # pickings linked to purchase order change state to assigned when a product is
        # added o changed
        pickings = purchase.picking_ids.filtered(lambda x: x.state == "assigned")
        pickings.action_assign()  # aka "Controlla disponibilità"
        new_product_move_line_ids = purchase.picking_ids.mapped('move_lines').filtered(
            lambda x: x.product_id == self.product5
        )
        self.assertTrue(new_product_move_line_ids.mapped("whs_list_ids"))
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0]),
            whs_len_records + 3)

        # test qty change on purchase order line, which create a new line with increased
        # qty on picking
        po_line.write({"product_qty": 27})
        pickings = po_line.order_id.picking_ids.filtered(
            lambda x: x.state == 'assigned')
        pickings.action_assign()
        po_whs_list = po_line.move_ids.mapped('whs_list_ids').filtered(
            lambda x: x.qta == 7
        )
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_select_query = \
            "SELECT Qta, QtaMovimentata FROM HOST_LISTE WHERE " \
            "NumLista = '%s' AND NumRiga = '%s'" % (
                po_whs_list.num_lista, po_whs_list.riga
            )
        result_liste = self.dbsource.execute_mssql(
            sqlquery=whs_select_query, sqlparams=None, metadata=None)
        # whs list is created for the increased qty
        self.assertEqual(str(result_liste[0]), "[(Decimal('7.000'), None)]")
