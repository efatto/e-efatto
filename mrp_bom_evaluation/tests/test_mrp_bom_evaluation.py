from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestProductionGroupLine(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_kgm = cls.env.ref('uom.product_uom_kgm')
        cls.uom_ton = cls.env.ref('uom.product_uom_ton')
        cls.uom_gr = cls.env.ref('uom.product_uom_gram')
        cls.uom_m = cls.env.ref('uom.product_uom_meter')
        cls.product_weight = cls.env['product.product'].create([{
            'name': 'Component',
            'uom_id': cls.uom_kgm.id,
            'uom_po_id': cls.uom_kgm.id}])
        cls.product_weight1 = cls.env['product.product'].create([{
            'name': 'Component 1',
            'uom_id': cls.uom_kgm.id,
            'uom_po_id': cls.uom_kgm.id}])
        cls.product_weight2 = cls.env['product.product'].create([{
            'name': 'Component 2',
            'uom_id': cls.uom_kgm.id,
            'uom_po_id': cls.uom_kgm.id}])
        cls.product_weight3 = cls.env['product.product'].create([{
            'name': 'Component 3 not weight uom',
            'uom_id': cls.uom_m.id,
            'uom_po_id': cls.uom_m.id,
            'weight': 13.55}])
        cls.bom_weight = cls.env['mrp.bom'].create([{
            'product_id': cls.top_product.id,
            'product_tmpl_id': cls.top_product.product_tmpl_id.id,
            'product_uom_id': cls.uom_unit.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {'product_id': cls.product_weight.id, 'product_qty': 2.55}),
                (0, 0, {'product_id': cls.product_weight1.id, 'product_qty': 8.13}),
                (0, 0, {'product_id': cls.product_weight2.id, 'product_qty': 12.01})
            ]}])

    def test_01_weight(self):
        self.assertEqual(len(self.bom_weight.bom_line_ids), 3)
        self.assertAlmostEqual(self.bom_weight.weight_total, 2.55 + 8.13 + 12.01)

        # Add a product with not-weight uom, to compute weight directly
        self.bom_weight.write({
            'bom_line_ids': [
                (0, 0, {'product_id': self.product_weight3.id, 'product_qty': 5.5})
            ]
        })
        self.assertAlmostEqual(self.bom_weight.weight_total,
                               2.55 + 8.13 + 12.01 + (13.55 * 5.5), 2)

        # Add a product with not-weight uom and different uom on weight (ton)
        product_weight4 = self.env['product.product'].create([{
            'name': 'Component 4 ton weight uom',
            'uom_id': self.uom_m.id,
            'uom_po_id': self.uom_m.id,
            'weight_uom_id': self.uom_ton.id,
            'weight': 3.73}])
        self.bom_weight.write({
            'bom_line_ids': [
                (0, 0, {'product_id': product_weight4.id, 'product_qty': 1.76})
            ]
        })
        self.assertEqual(len(self.bom_weight.bom_line_ids), 5)
        self.assertAlmostEqual(self.bom_weight.bom_line_ids.filtered(
            lambda x: x.product_id == product_weight4
        ).weight_total, 3.73 * 1.76 * 1000, places=2)
        self.assertAlmostEqual(self.bom_weight.weight_total,
                               (2.55 + 8.13 + 12.01 + (13.55 * 5.5)
                                + (3.73 * 1.76 * 1000)), places=1)

        # Add a product with not-weight uom and different uom on weight (ton)
        product_weight5 = self.env['product.product'].create([{
            'name': 'Component 5 gram weight uom',
            'uom_id': self.uom_m.id,
            'uom_po_id': self.uom_m.id,
            'weight_uom_id': self.uom_gr.id,
            'weight': 1550}])
        self.bom_weight.write({
            'bom_line_ids': [
                (0, 0, {'product_id': product_weight5.id, 'product_qty': 1.18})
            ]
        })
        self.assertAlmostEqual(self.bom_weight.bom_line_ids.filtered(
            lambda x: x.product_id == product_weight5
        ).weight_total, 1550 * 1.18 / 1000, places=2)
        self.assertAlmostEqual(self.bom_weight.weight_total,
                               (2.55 + 8.13 + 12.01 + (13.55 * 5.5)
                                + (3.73 * 1.76 * 1000)
                                + (1550 * 1.18 / 1000)), places=1)
