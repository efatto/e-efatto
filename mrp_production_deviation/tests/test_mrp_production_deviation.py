# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData
from odoo.tests import Form


class TestMrpProductionDeviation(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

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
        self.assertEqual(deviation_data[0].get('product_id')[0], self.subproduct_1_1.id)
        self.assertAlmostEqual(deviation_data[0].get('cost'), 0)
        self.assertAlmostEqual(deviation_data[0].get('unit_cost'),
                               self.subproduct_1_1.standard_price)
        self.assertAlmostEqual(deviation_data[0].get('duration_expected'), 0)
        self.assertAlmostEqual(deviation_data[0].get('duration_expected_rw'), 0)
        self.assertAlmostEqual(deviation_data[0].get('quantity_expected'),
                               3 * production_qty)
        self.assertAlmostEqual(deviation_data[0].get('product_qty'), 0)
        self.assertAlmostEqual(
            deviation_data[0].get('cost_expected'),
            (10 * production_qty) * self.subproduct_1_1.standard_price)
        self.assertAlmostEqual(deviation_data[0].get('cost_expected_rw'), 0)

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
        # procuce partially
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
        self.assertEqual(deviation_data_2[0].get('product_id')[0],
                         self.subproduct_1_1.id)
        self.assertAlmostEqual(deviation_data_2[0].get('cost'),
                               self.subproduct_1_1.standard_price * 16 * produced_qty)
        self.assertAlmostEqual(deviation_data_2[0].get('quantity_expected'),
                               3 * production_qty)
        self.assertAlmostEqual(deviation_data_2[0].get('product_qty'),
                               16 * produced_qty)
        self.assertAlmostEqual(deviation_data_2[0].get('cost_expected'),
                               (10 * production_qty) * 10)
        self.assertAlmostEqual(deviation_data_2[0].get('cost_expected_rw'), 0)
        workorders_data_1 = [x for x in deviation_data_2 if not x['product_id']]
        self.assertAlmostEqual(workorders_data_1[0].get('duration_expected_rw'),
                               duration_expected_rw)
        self.assertAlmostEqual(workorders_data_1[0].get('duration_expected'),
                               duration_expected)
        self.assertAlmostEqual(workorders_data_1[0].get('cost_expected'),
                               duration_expected / 60 * self.workcenter1.costs_hour)
        self.assertAlmostEqual(workorders_data_1[0].get('cost_expected_rw'),
                               duration_expected_rw / 60 * self.workcenter1.costs_hour)
        # complete production
        produce_form.product_qty = 3.0
        produced_qty += produce_form.product_qty
        wizard_1 = produce_form.save()
        wizard_1.do_produce()
        man_order.button_mark_done()
        self.assertEqual(man_order.state, 'done')
        deviation_data_3 = self.get_deviation_data(man_order)
        self.assertTrue(deviation_data_3)
        self.assertEqual(deviation_data_3[0].get('product_id')[0],
                         self.subproduct_1_1.id)
        self.assertAlmostEqual(deviation_data_3[0].get('cost'),
                               self.subproduct_1_1.standard_price * 16 * produced_qty)
        self.assertAlmostEqual(deviation_data_3[0].get('unit_cost'), 10)
        self.assertAlmostEqual(deviation_data_3[0].get('quantity_expected'),
                               3 * production_qty)
        self.assertAlmostEqual(deviation_data_3[0].get('product_qty'),
                               16 * produced_qty)
        self.assertAlmostEqual(deviation_data_3[0].get('cost_expected'),
                               (10 * production_qty) * 10)
        self.assertAlmostEqual(deviation_data_3[0].get('cost_expected_rw'), 0)

        old_standard_price = self.subproduct_1_1.standard_price
        self.subproduct_1_1.standard_price = 33.45
        deviation_data_4 = self.get_deviation_data(man_order)
        self.assertAlmostEqual(deviation_data_4[0].get('cost'),
                               old_standard_price * 16 * produced_qty)
        self.assertAlmostEqual(deviation_data_4[0].get('cost_current'),
                               self.subproduct_1_1.standard_price * 16 * produced_qty)
