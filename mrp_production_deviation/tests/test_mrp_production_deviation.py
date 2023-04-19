# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData
from odoo.tests import Form
from odoo import fields
from odoo.tools.date_utils import relativedelta


class TestMrpProductionDeviation(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_2 = cls.env['product.product'].create([{
            'name': 'Additional component product',
            'type': 'product',
            'default_code': 'ADDCOMP',
            'standard_price': 7.0,
            'route_ids': [
                (4, cls.env.ref('purchase_stock.route_warehouse0_buy').id)],
            'seller_ids': [
                (0, 0, {
                    'name': cls.env.ref('base.res_partner_3').id,
                    'price': 5.0,
                    'min_qty': 0.0,
                    'sequence': 1,
                    'date_start': fields.Date.today() - relativedelta(days=100),
                    'delay': 28,
                }),
            ]
        }])

    def get_deviation_data(self, production):
        res = self.env['mrp.production.deviation.report'].read_group(
            [('production_id', '=', production.id)],
            ['product_id', 'unit_cost', 'cost', 'cost_expected', 'cost_expected_rw',
             'duration_expected', 'duration_expected_rw', 'workorder_id',
             'quantity_expected', 'product_qty', 'cost_current'],
            ['product_id'])
        return res

    def test_01_mo_deviation_data(self):
        production_qty = 5
        self.main_bom.routing_id = self.routing1
        man_order = self.env['mrp.production'].create({
            'name': 'MO-Test',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': production_qty,
            'bom_id': self.main_bom.id,
        })
        deviation_data = self.get_deviation_data(man_order)
        self.assertTrue(deviation_data)
        subproduct_1_1_deviation_datas = [
            x for x in deviation_data if x['product_id'][0] == self.subproduct_1_1.id]
        self.assertAlmostEqual(
            sum(x['cost'] for x in subproduct_1_1_deviation_datas), 0)
        self.assertAlmostEqual(
            max(x['unit_cost'] for x in subproduct_1_1_deviation_datas),
            self.subproduct_1_1.standard_price)
        self.assertAlmostEqual(
            sum(x['duration_expected'] for x in subproduct_1_1_deviation_datas), 0)
        self.assertAlmostEqual(
            sum(x['duration_expected_rw'] for x in subproduct_1_1_deviation_datas), 0)
        self.assertAlmostEqual(
            sum(x['quantity_expected'] for x in subproduct_1_1_deviation_datas),
            ((3 * 2) + (5 * 2)) * production_qty)
        self.assertAlmostEqual(
            sum(x['product_qty'] for x in subproduct_1_1_deviation_datas), 0)
        self.assertAlmostEqual(
            sum(x['cost_expected'] for x in subproduct_1_1_deviation_datas),
            ((3 * 2) + (5 * 2)) * production_qty * self.subproduct_1_1.standard_price)
        self.assertAlmostEqual(
            sum(x['cost_expected_rw'] for x in subproduct_1_1_deviation_datas), 0)

        # create workorder to add relative costs
        man_order.action_assign()
        man_order.button_plan()
        deviation_data_1 = self.get_deviation_data(man_order)
        duration_expected = (
            (
                self.operation1.time_cycle_manual / (
                    self.workcenter1.time_efficiency / 100)
            ) * production_qty
            + self.workcenter1.time_start
            + self.workcenter1.time_stop
        )
        duration_expected_rw = self.operation1.time_cycle_manual * production_qty
        workorders_data = [x for x in deviation_data_1 if not x['product_id']]
        self.assertAlmostEqual(workorders_data[0].get('duration_expected_rw'),
                               duration_expected_rw)
        self.assertAlmostEqual(workorders_data[0].get('duration_expected'),
                               duration_expected)
        self.assertAlmostEqual(workorders_data[0].get('cost_expected'),
                               duration_expected / 60 * self.workcenter1.costs_hour)
        self.assertAlmostEqual(workorders_data[0].get('cost_expected_rw'),
                               duration_expected_rw / 60 * self.workcenter1.costs_hour)
        self.assertEqual(deviation_data[0], deviation_data_1[0])
        self.assertEqual(deviation_data[1], deviation_data_1[1])
        # produce partially
        produce_form = Form(
            self.env['mrp.product.produce'].with_context(
                active_id=man_order.id,
                active_ids=[man_order.id],
            )
        )
        produced_qty = 2.0
        produce_form.product_qty = produced_qty
        wizard = produce_form.save()
        wizard.do_produce()

        deviation_data_2 = self.get_deviation_data(man_order)
        self.assertTrue(deviation_data_2)
        subproduct_1_1_deviation_datas_2 = [
            x for x in deviation_data_2 if x.get('product_id', False)
            and x['product_id'][0] == self.subproduct_1_1.id]
        self.assertAlmostEqual(
            sum(x['cost'] for x in subproduct_1_1_deviation_datas_2),
            self.subproduct_1_1.standard_price * 16 * produced_qty)
        self.assertAlmostEqual(
            sum(x['quantity_expected'] for x in subproduct_1_1_deviation_datas_2),
            ((3 * 2) + (5 * 2)) * production_qty)
        self.assertAlmostEqual(
            sum(x['product_qty'] for x in subproduct_1_1_deviation_datas_2),
            16 * produced_qty)
        self.assertAlmostEqual(
            sum(x['cost_expected'] for x in subproduct_1_1_deviation_datas_2),
            ((3 * 2) + (5 * 2)) * production_qty * self.subproduct_1_1.standard_price)
        self.assertAlmostEqual(
            sum(x['cost_expected_rw'] for x in subproduct_1_1_deviation_datas_2),
            0)
        workorders_data_1 = [x for x in deviation_data_2 if not x['product_id']]
        self.assertAlmostEqual(workorders_data_1[0].get('duration_expected_rw'),
                               duration_expected_rw)
        self.assertAlmostEqual(workorders_data_1[0].get('duration_expected'),
                               duration_expected)
        self.assertAlmostEqual(workorders_data_1[0].get('cost_expected'),
                               duration_expected / 60 * self.workcenter1.costs_hour)
        self.assertAlmostEqual(workorders_data_1[0].get('cost_expected_rw'),
                               duration_expected_rw / 60 * self.workcenter1.costs_hour)

        # todo aggiungere delle righe extra-bom
        man_order.action_toggle_is_locked()
        man_order.write({
            'move_raw_ids': [
                (0, 0, {
                    'name': self.product_2.name,
                    'product_id': self.product_2.id,
                    'product_uom': self.product_2.uom_id.id,
                    'location_id': man_order.location_src_id.id,
                    'location_dest_id': man_order.location_dest_id.id,
                    'state': 'confirmed',
                    'raw_material_production_id': man_order.id,
                    'picking_type_id': man_order.picking_type_id.id,
                }),
            ]
        })
        man_order.action_toggle_is_locked()
        move_raw = man_order.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_2
        )
        self.env['mrp.production.component.change'].with_context(
            active_id=move_raw.id,
            active_model='stock.move',
        ).create([{
            'product_uom_qty': 3,
        }]).action_done()
        self.assertEqual(len(man_order.move_raw_ids), 4)
        self.assertEqual(move_raw.product_uom_qty, 3)
        self.assertEqual(move_raw.quantity_done, 0)

        # complete production, changing quantity done for additional component
        produce_form.product_qty = 3.0
        produced_qty += produce_form.product_qty
        wizard_1 = produce_form.save()
        wizard_1.do_produce()
        move_raw.write({'quantity_done': 3})
        self.assertEqual(move_raw.quantity_done, 3)
        move_raw_sub_2_1 = man_order.move_raw_ids.filtered(
            lambda x: x.product_id == self.subproduct_2_1
        )
        sml_ids = self.env['stock.move.line'].search([
            ('move_id', '=', move_raw_sub_2_1.id)])
        self.assertAlmostEqual(move_raw_sub_2_1.quantity_done, 40.0)
        sml_ids.unlink()
        self.assertAlmostEqual(move_raw_sub_2_1.quantity_done, 0.0)
        man_order.button_mark_done()
        self.assertEqual(man_order.state, 'done')
        deviation_data_3 = self.get_deviation_data(man_order)
        self.assertTrue(deviation_data_3)
        subproduct_1_1_deviation_datas_3 = [
            x for x in deviation_data_3 if x.get('product_id', False)
            and x['product_id'][0] == self.subproduct_1_1.id]
        self.assertAlmostEqual(
            sum(x['cost'] for x in subproduct_1_1_deviation_datas_3),
            self.subproduct_1_1.standard_price * 16 * produced_qty)
        self.assertAlmostEqual(
            sum(x['unit_cost'] for x in subproduct_1_1_deviation_datas_3), 10)
        self.assertAlmostEqual(
            sum(x['quantity_expected'] for x in subproduct_1_1_deviation_datas_3),
            ((3 * 2) + (5 * 2)) * production_qty)
        self.assertAlmostEqual(
            sum(x['product_qty'] for x in subproduct_1_1_deviation_datas_3),
            16 * produced_qty)
        self.assertAlmostEqual(
            sum(x['cost_expected'] for x in subproduct_1_1_deviation_datas_3),
            ((3 * 2) + (5 * 2)) * production_qty * self.subproduct_1_1.standard_price)
        self.assertAlmostEqual(
            sum(x['cost_expected_rw'] for x in subproduct_1_1_deviation_datas_3), 0)

        old_standard_price = self.subproduct_1_1.standard_price
        self.subproduct_1_1.standard_price = 33.45
        deviation_data_4 = self.get_deviation_data(man_order)
        subproduct_1_1_deviation_datas_4 = [
            x for x in deviation_data_4 if x.get('product_id', False)
            and x['product_id'][0] == self.subproduct_1_1.id]
        self.assertAlmostEqual(sum(x['cost'] for x in subproduct_1_1_deviation_datas_4),
                               old_standard_price * 16 * produced_qty)
        self.assertAlmostEqual(
            sum(x['cost_current'] for x in subproduct_1_1_deviation_datas_4),
            self.subproduct_1_1.standard_price * 16 * produced_qty)
        self.subproduct_1_1.standard_price = 10

        # check product_2 has correct report values
        product_2_deviation_datas_4 = [
            x for x in deviation_data_4 if x.get('product_id', False)
            and x['product_id'][0] == self.product_2.id]
        self.assertAlmostEqual(
            sum(x['cost_expected'] for x in product_2_deviation_datas_4), 0)
        self.assertAlmostEqual(
            sum(x['quantity_expected'] for x in product_2_deviation_datas_4), 0)
        self.assertAlmostEqual(
            sum(x['product_qty'] for x in product_2_deviation_datas_4), 3)
        self.assertAlmostEqual(
            sum(x['cost_current'] for x in product_2_deviation_datas_4),
            3 * self.product_2.standard_price)

        # check subproduct_2_1 has correct report values
        subproduct_2_1_deviation_datas_4 = [
            x for x in deviation_data_4 if x.get('product_id', False)
            and x['product_id'][0] == self.subproduct_2_1.id]
        self.assertAlmostEqual(
            sum(x['cost_expected'] for x in subproduct_2_1_deviation_datas_4),
            8 * self.subproduct_2_1.standard_price * produced_qty)
        self.assertAlmostEqual(
            sum(x['quantity_expected'] for x in subproduct_2_1_deviation_datas_4),
            8 * produced_qty)
        self.assertAlmostEqual(
            sum(x['product_qty'] for x in subproduct_2_1_deviation_datas_4), 0)
        self.assertAlmostEqual(
            sum(x['cost'] for x in subproduct_2_1_deviation_datas_4), 0)

    def test_02_mo_deviation_data_serial(self):
        production_qty = 5
        self.main_bom.routing_id = self.routing1
        self.top_product.tracking = "serial"
        man_order = self.env['mrp.production'].create({
            'name': 'MO-Test',
            'product_id': self.top_product.id,
            'product_uom_id': self.top_product.uom_id.id,
            'product_qty': production_qty,
            'bom_id': self.main_bom.id,
        })
        # force qty change to create finished product rows to let user assign lots
        if man_order.routing_id and man_order.product_id.tracking != 'none':
            self.env['change.production.qty'].create({
                'mo_id': man_order.id,
                'product_qty': man_order.product_qty,
            }).change_prod_qty()
        for finished_move_line in man_order.finished_move_line_ids:
            lot = self.env['stock.production.lot'].create({
                'name': 'Final lot %s' % (finished_move_line.id),
                'product_id': self.top_product.id,
            })
            finished_move_line.write({"lot_id": lot.id})

        deviation_data = self.get_deviation_data(man_order)
        self.assertTrue(deviation_data)
        subproduct_1_1_deviation_datas = [
            x for x in deviation_data if x['product_id'][0] == self.subproduct_1_1.id]
        self.assertAlmostEqual(
            sum(x['cost'] for x in subproduct_1_1_deviation_datas), 0)
        self.assertAlmostEqual(
            max(x['unit_cost'] for x in subproduct_1_1_deviation_datas),
            self.subproduct_1_1.standard_price)
        self.assertAlmostEqual(
            sum(x['duration_expected'] for x in subproduct_1_1_deviation_datas), 0)
        self.assertAlmostEqual(
            sum(x['duration_expected_rw'] for x in subproduct_1_1_deviation_datas), 0)
        self.assertAlmostEqual(
            sum(x['quantity_expected'] for x in subproduct_1_1_deviation_datas),
            ((3 * 2) + (5 * 2)) * production_qty)
        self.assertAlmostEqual(
            sum(x['product_qty'] for x in subproduct_1_1_deviation_datas), 0)
        self.assertAlmostEqual(
            sum(x['cost_expected'] for x in subproduct_1_1_deviation_datas),
            ((3 * 2) + (5 * 2)) * production_qty * self.subproduct_1_1.standard_price)
        self.assertAlmostEqual(
            sum(x['cost_expected_rw'] for x in subproduct_1_1_deviation_datas), 0)

        # create workorder to add relative costs
        man_order.action_assign()
        man_order.button_plan()
        deviation_data_1 = self.get_deviation_data(man_order)
        duration_expected = (
            (
                self.operation1.time_cycle_manual / (
                    self.workcenter1.time_efficiency / 100)
            ) * production_qty
            + self.workcenter1.time_start
            + self.workcenter1.time_stop
        )
        duration_expected_rw = self.operation1.time_cycle_manual * production_qty
        workorders_data = [x for x in deviation_data_1 if not x['product_id']]
        self.assertAlmostEqual(workorders_data[0].get('duration_expected_rw'),
                               duration_expected_rw)
        self.assertAlmostEqual(workorders_data[0].get('duration_expected'),
                               duration_expected)
        self.assertAlmostEqual(workorders_data[0].get('cost_expected'),
                               duration_expected / 60 * self.workcenter1.costs_hour)
        self.assertAlmostEqual(workorders_data[0].get('cost_expected_rw'),
                               duration_expected_rw / 60 * self.workcenter1.costs_hour)
        self.assertEqual(deviation_data[0], deviation_data_1[0])
        self.assertEqual(deviation_data[1], deviation_data_1[1])
        produced_qty = 2
        for workorder in man_order.workorder_ids:
            workorder.sudo(self.mrp_user).button_start()
            # start all workorders and produce 2 products each
            for n in range(0, produced_qty):
                if not workorder.next_work_order_id:
                    workorder.final_lot_id = man_order.finished_move_line_ids[n].lot_id
                workorder.sudo(self.mrp_user).record_production()
        deviation_data_2 = self.get_deviation_data(man_order)
        self.assertTrue(deviation_data_2)
        subproduct_1_1_deviation_datas_2 = [
            x for x in deviation_data_2 if x.get('product_id', False)
            and x['product_id'][0] == self.subproduct_1_1.id]
        self.assertAlmostEqual(
            sum(x['cost'] for x in subproduct_1_1_deviation_datas_2),
            self.subproduct_1_1.standard_price * 16 * produced_qty)
        self.assertAlmostEqual(
            sum(x['quantity_expected'] for x in subproduct_1_1_deviation_datas_2),
            ((3 * 2) + (5 * 2)) * production_qty)
        self.assertAlmostEqual(
            sum(x['product_qty'] for x in subproduct_1_1_deviation_datas_2),
            16 * produced_qty)
        self.assertAlmostEqual(
            sum(x['cost_expected'] for x in subproduct_1_1_deviation_datas_2),
            ((3 * 2) + (5 * 2)) * production_qty * self.subproduct_1_1.standard_price)
        self.assertAlmostEqual(
            sum(x['cost_expected_rw'] for x in subproduct_1_1_deviation_datas_2),
            0)
        workorders_data_1 = [x for x in deviation_data_2 if not x['product_id']]
        self.assertAlmostEqual(workorders_data_1[0].get('duration_expected_rw'),
                               duration_expected_rw)
        self.assertAlmostEqual(workorders_data_1[0].get('duration_expected'),
                               duration_expected)
        self.assertAlmostEqual(workorders_data_1[0].get('cost_expected'),
                               duration_expected / 60 * self.workcenter1.costs_hour)
        self.assertAlmostEqual(workorders_data_1[0].get('cost_expected_rw'),
                               duration_expected_rw / 60 * self.workcenter1.costs_hour)

        man_order.action_toggle_is_locked()
        man_order.write({
            'move_raw_ids': [
                (0, 0, {
                    'name': self.product_2.name,
                    'product_id': self.product_2.id,
                    'product_uom': self.product_2.uom_id.id,
                    'location_id': man_order.location_src_id.id,
                    'location_dest_id': man_order.location_dest_id.id,
                    'state': 'confirmed',
                    'raw_material_production_id': man_order.id,
                    'picking_type_id': man_order.picking_type_id.id,
                }),
            ]
        })
        man_order.action_toggle_is_locked()
        move_raw = man_order.move_raw_ids.filtered(
            lambda x: x.product_id == self.product_2
        )
        self.env['mrp.production.component.change'].with_context(
            active_id=move_raw.id,
            active_model='stock.move',
        ).create([{
            'product_uom_qty': 3,
        }]).action_done()
        self.assertEqual(len(man_order.move_raw_ids), 4)
        self.assertEqual(move_raw.product_uom_qty, 3)
        self.assertEqual(move_raw.quantity_done, 0)

        # complete production, changing quantity done for additional component
        produced_qty += 3
        for workorder in man_order.workorder_ids:
            workorder.sudo(self.mrp_user).button_start()
            # produce residual 3 products
            for n in range(0, 3):
                if not workorder.next_work_order_id:
                    workorder.final_lot_id = man_order.finished_move_line_ids[
                        n+2].lot_id
                workorder.sudo(self.mrp_user).record_production()
        # force quantity_done for product_2 and assign lot produced
        move_raw.write({'quantity_done': 3})
        move_raw._action_confirm()
        move_raw.active_move_line_ids[0].write({
            "lot_produced_id": man_order.finished_move_line_ids[0].lot_id.id,
        })
        self.assertEqual(move_raw.quantity_done, 3)
        move_raw_sub_2_1 = man_order.move_raw_ids.filtered(
            lambda x: x.product_id == self.subproduct_2_1
        )
        sml_ids = self.env['stock.move.line'].search([
            ('move_id', '=', move_raw_sub_2_1.id)])
        self.assertAlmostEqual(move_raw_sub_2_1.quantity_done, 40.0)
        sml_ids.unlink()
        self.assertAlmostEqual(move_raw_sub_2_1.quantity_done, 0.0)
        man_order.button_mark_done()
        self.assertEqual(man_order.state, 'done')
        deviation_data_3 = self.get_deviation_data(man_order)
        self.assertTrue(deviation_data_3)
        subproduct_1_1_deviation_datas_3 = [
            x for x in deviation_data_3 if x.get('product_id', False)
            and x['product_id'][0] == self.subproduct_1_1.id]
        self.assertAlmostEqual(
            sum(x['cost'] for x in subproduct_1_1_deviation_datas_3),
            self.subproduct_1_1.standard_price * 16 * produced_qty)
        self.assertAlmostEqual(
            sum(x['unit_cost'] for x in subproduct_1_1_deviation_datas_3), 10)
        self.assertAlmostEqual(
            sum(x['quantity_expected'] for x in subproduct_1_1_deviation_datas_3),
            ((3 * 2) + (5 * 2)) * production_qty)
        self.assertAlmostEqual(
            sum(x['product_qty'] for x in subproduct_1_1_deviation_datas_3),
            16 * produced_qty)
        self.assertAlmostEqual(
            sum(x['cost_expected'] for x in subproduct_1_1_deviation_datas_3),
            ((3 * 2) + (5 * 2)) * production_qty * self.subproduct_1_1.standard_price)
        self.assertAlmostEqual(
            sum(x['cost_expected_rw'] for x in subproduct_1_1_deviation_datas_3), 0)

        old_standard_price = self.subproduct_1_1.standard_price
        self.subproduct_1_1.standard_price = 33.45
        deviation_data_4 = self.get_deviation_data(man_order)
        subproduct_1_1_deviation_datas_4 = [
            x for x in deviation_data_4 if x.get('product_id', False)
            and x['product_id'][0] == self.subproduct_1_1.id]
        self.assertAlmostEqual(sum(x['cost'] for x in subproduct_1_1_deviation_datas_4),
                               old_standard_price * 16 * produced_qty)
        self.assertAlmostEqual(
            sum(x['cost_current'] for x in subproduct_1_1_deviation_datas_4),
            self.subproduct_1_1.standard_price * 16 * produced_qty)
        self.subproduct_1_1.standard_price = 10

        # check product_2 has correct report values
        product_2_deviation_datas_4 = [
            x for x in deviation_data_4 if x.get('product_id', False)
            and x['product_id'][0] == self.product_2.id]
        self.assertAlmostEqual(
            sum(x['cost_expected'] for x in product_2_deviation_datas_4), 0)
        self.assertAlmostEqual(
            sum(x['quantity_expected'] for x in product_2_deviation_datas_4), 0)
        self.assertAlmostEqual(
            sum(x['product_qty'] for x in product_2_deviation_datas_4), 3)
        self.assertAlmostEqual(
            sum(x['cost_current'] for x in product_2_deviation_datas_4),
            3 * self.product_2.standard_price)

        # check subproduct_2_1 has correct report values
        subproduct_2_1_deviation_datas_4 = [
            x for x in deviation_data_4 if x.get('product_id', False)
            and x['product_id'][0] == self.subproduct_2_1.id]
        self.assertAlmostEqual(
            sum(x['cost_expected'] for x in subproduct_2_1_deviation_datas_4),
            8 * self.subproduct_2_1.standard_price * produced_qty)
        self.assertAlmostEqual(
            sum(x['quantity_expected'] for x in subproduct_2_1_deviation_datas_4),
            8 * produced_qty)
        self.assertAlmostEqual(
            sum(x['product_qty'] for x in subproduct_2_1_deviation_datas_4), 0)
        self.assertAlmostEqual(
            sum(x['cost'] for x in subproduct_2_1_deviation_datas_4), 0)
