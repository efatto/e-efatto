# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestProductionData(common.TransactionCase):

    def setUp(self, *args, **kwargs):
        super(TestProductionData, self).setUp(*args, **kwargs)
        self.production_model = self.env['mrp.production']
        self.procurement_model = self.env['procurement.group']
        self.bom_model = self.env['mrp.bom']
        self.stock_location_stock = self.env.ref('stock.stock_location_stock')
        self.manufacture_route = self.env.ref(
            'mrp.route_warehouse0_manufacture')
        self.uom_unit = self.env.ref('uom.product_uom_unit')
        self.warehouse = self.env.ref('stock.warehouse0')
        self.top_product = self.env.ref(
            'mrp_production_demo.product_product_manufacture_1')
        self.subproduct1 = self.env.ref(
            'mrp_production_demo.product_product_manufacture_1_1')
        self.subproduct2 = self.env.ref(
            'mrp_production_demo.product_product_manufacture_1_2')
        self.subproduct_1_1 = self.env.ref(
            'mrp_production_demo.product_product_manufacture_1_1_1')
        self.subproduct_2_1 = self.env.ref(
            'mrp_production_demo.product_product_manufacture_1_2_1')
        self.main_bom = self.env.ref('mrp_production_demo.mrp_bom_manuf_1')
        self.sub_bom1 = self.env.ref('mrp_production_demo.mrp_bom_manuf_1_1')
        self.sub_bom2 = self.env.ref('mrp_production_demo.mrp_bom_manuf_1_2')
        self.workcenter1 = self.env['mrp.workcenter'].create({
            'name': 'Base Workcenter',
            'capacity': 1,
            'time_start': 10,
            'time_stop': 5,
            'time_efficiency': 80,
        })
        self.routing1 = self.env['mrp.routing'].create({
            'name': 'Simple routing',
        })
        self.operation1 = self.env['mrp.routing.workcenter'].create({
            'name': 'Operation 1',
            'workcenter_id': self.workcenter1.id,
            'routing_id': self.routing1.id,
            'time_cycle': 15,
            'sequence': 1,
        })
