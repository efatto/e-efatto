# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.addons.base_external_dbsource.exceptions import ConnectionSuccessError
from odoo.tests import tagged
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
        self.partner = self.env.ref('base.res_partner_2')
        # Acoustic Bloc Screens, 16 on hand
        self.product1 = self.env.ref('product.product_product_25')
        # Cabinet with Doors, 8 on hand
        self.product2 = self.env.ref('product.product_product_10')
        # Large Cabinet, 250 on hand
        self.product3 = self.env.ref('product.product_product_6')
        # Drawer Black, 0 on hand
        self.product4 = self.env.ref('product.product_product_16')
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
        self.assertEqual(len(order1.picking_ids.move_lines.whs_list_ids), 1)
        self.assertEqual(order1.mapped('picking_ids.state'), ['waiting'])
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

        whs_list = order1.picking_ids.move_lines.whs_list_ids[0]
        # simulate whs work
        # todo inserire un while per verificare se è stato fatto e attendere
        #  l'intervento utente su WHS
        set_liste_elaborated_query = \
            "UPDATE HOST_LISTE SET Elaborato=4, QtaMovimentata=%s WHERE " \
            "NumLista = '%s' AND NumRiga = '%s'" % (
                whs_list.qta, whs_list.num_lista, whs_list.riga
            )
        self.dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=set_liste_elaborated_query, sqlparams=None, metadata=None)

        whs_select_query = \
            "SELECT Qta, QtaMovimentata FROM HOST_LISTE WHERE Elaborato = 4 AND " \
            "NumLista = '%s' AND NumRiga = '%s'" % (
                whs_list.num_lista, whs_list.riga
            )
        result_liste = self.dbsource.execute_mssql(
            sqlquery=whs_select_query, sqlparams=None, metadata=None)
        self.assertEqual(str(result_liste[0]),
                         "[(Decimal('5.000'), Decimal('5.000'))]")

        self.dbsource.whs_insert_read_and_synchronize_list()

        # check move and picking linked to sale order have changed state to done
        self.assertEqual(order1.picking_ids.move_lines[0].state, 'assigned')
        self.assertEqual(order1.picking_ids[0].state, 'assigned')

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
        self.assertEqual(order1.mapped('picking_ids.state'), ['waiting'])
        picking = order1.picking_ids[0]
        self.assertEqual(len(picking.mapped('move_lines.whs_list_ids')), 2)

        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0]
        self.assertEqual(len(whs_records), whs_len_records + 2)
        for whs_record in whs_records:
            self.assertTrue(order1.client_order_ref in whs_record.values())
            if self.product1.default_code in whs_record.values():
                self.assertTrue(self.product1.customer_ids[0].product_code in
                                whs_record.values())
            else:
                self.assertFalse(self.product1.customer_ids[0].product_code in
                                 whs_record.values())

        whs_list = picking.mapped('move_lines.whs_list_ids')[0]
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
        self.assertEqual(str(result_liste[0]),
                         "[(Decimal('5.000'), Decimal('3.000'), 1)]")

        self.dbsource.whs_insert_read_and_synchronize_list()

        # check move and picking linked to sale order have changed state to done
        self.assertEqual(picking.move_lines[0].state, 'assigned')
        self.assertAlmostEqual(picking.move_lines[0].move_line_ids[0].qty_done, 3.0)
        self.assertEqual(picking.state, 'assigned')

        # simulate user partial validate of picking and check backorder exist
        backorder_wiz_id = picking.button_validate()['res_id']
        backorder_wiz = self.env['stock.backorder.confirmation'].browse(
            backorder_wiz_id)
        # User cannot create backorder if whs list is not processed on whs system

        # with self.assertRaises(UserError):
        backorder_wiz.process()

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
        # check whs list for backorder is created
        self.dbsource.whs_insert_read_and_synchronize_list()
        self.assertEqual(len(self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0]),
            whs_len_records + 3)

        # check back picking is waiting for whs process
        self.assertEqual(len(order1.picking_ids), 2)
        backorder_picking = order1.picking_ids - picking
        self.assertEqual(backorder_picking.state, 'waiting')
        self.assertEqual(backorder_picking.move_lines[0].state, 'waiting')

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
        self.assertEqual(picking.state, 'waiting')

        # check whs list is added
        self.dbsource.whs_insert_read_and_synchronize_list()
        whs_records = self.dbsource.execute_mssql(
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0]
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
        self.assertEqual(backorder_picking.move_lines.mapped('state'), ['waiting'])
        # todo check also a 'partially_available'
        self.assertEqual(backorder_picking.state, 'waiting')

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
        self.assertEqual(order1.mapped('picking_ids.state'), ['waiting'])
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
        self.assertEqual(picking.move_lines[0].state, 'assigned')
        self.assertAlmostEqual(picking.move_lines[0].move_line_ids[0].qty_done, 5.0)
        self.assertEqual(picking.state, 'assigned')

        # simulate user partial validate of picking and check backorder exist
        backorder_wiz_id = picking.button_validate()['res_id']
        backorder_wiz = self.env['stock.backorder.confirmation'].browse(
            backorder_wiz_id)
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

        # check back picking is waiting for whs process
        self.assertEqual(backorder_picking.state, 'waiting')
        self.assertEqual(backorder_picking.mapped('move_lines.state'),
                         ['waiting', 'waiting', 'waiting'])

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
        self.assertEqual(order1.mapped('picking_ids.state'), ['waiting'])
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
        picking = order1.picking_ids.filtered(lambda x: x.state == 'waiting')
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
            sqlquery="SELECT * FROM HOST_LISTE", sqlparams=None, metadata=None)[0]),
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
            self.assertEqual(
                str(result_liste[0]),
                "[(Decimal('5.000'), Decimal('2.000'))]"
                if whs_list.product_id == self.product2 else
                "[(Decimal('3.000'), Decimal('3.000'))]")

    def _create_purchase_order_line(self, order, product, qty):
        line = self.env['purchase.order.line'].create({
            'order_id': order.id,
            'product_id': product.id,
            'product_uom': product.uom_po_id.id,
            'name': product.name,
            'product_qty': qty,
            'price_unit': 100,
            'date_planned': fields.Datetime.today(),
            })
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
        self._create_purchase_order_line(purchase, self.product2, 20)
        self._create_purchase_order_line(purchase, self.product3, 3)
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
        picking.action_pack_operation_auto_fill()
        backorder_wiz_id = picking.button_validate()['res_id']
        backorder_wiz = self.env['stock.backorder.confirmation'].browse(
            backorder_wiz_id)
        backorder_wiz.process()
        self.assertEqual(picking.state, 'done')

        # check back picking is waiting as waiting for WHS work
        self.assertEqual(len(purchase.picking_ids), 2)
        backorder_picking = purchase.picking_ids - picking
        self.assertEqual(backorder_picking.move_lines.mapped('state'),
                         ['waiting'])
        self.assertEqual(backorder_picking.state, 'waiting')

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
        self.assertEqual(backorder_picking.state, 'done')
