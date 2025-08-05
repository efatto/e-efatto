from odoo.tests import Form

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestProductionGroupLine(TestProductionData):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_mo_by_product(self):
        self._update_product_qty(self.subproduct_1_1, 16 * 3)
        self._update_product_qty(self.subproduct_2_1, 8 * 3)
        production_form = Form(self.production_model)
        production_form.product_id = self.top_product
        production_form.product_qty = 1
        production_form.product_uom_id = self.uom_unit
        production_form.bom_id = self.main_bom
        production = production_form.save()
        production.action_confirm()
        production.action_assign()
        self.assertEqual(self.subproduct_1_1.virtual_available, 16 * 2)
        self.assertEqual(len(production.move_raw_ids), 3)
        wizard_form = Form(
            self.env["production.group.line.wizard"].with_context(
                active_id=production.id, active_model="mrp.production"
            )
        )
        wizard = wizard_form.save()
        wizard.action_done()
        self.assertEqual(len(production), 1)
        self.assertEqual(len(production.move_raw_ids), 2)
        # subproduct_1_1 consumption: 5*2=10 in sub1, 2*3=6 in sub2, tot=16
        self.assertEqual(
            production.move_raw_ids.filtered(
                lambda x: x.product_id == self.subproduct_1_1
            ).product_uom_qty,
            16,
        )

        # check change.production.qty is callable and it doesn't split lines, so
        # it multiply qty * 3
        change_qty_form = Form(
            self.env["change.production.qty"].with_context(
                active_id=production.id, active_model="mrp.production"
            )
        )
        change_qty_form.product_qty = 3.0
        change_qty_wizard = change_qty_form.save()
        change_qty_wizard.change_prod_qty()
        self.assertEqual(len(production.move_raw_ids), 2)
        # call of the wizard again do nothing
        wizard_obj = self.env["production.group.line.wizard"]
        wizard_vals = wizard_obj.with_context(
            active_id=production.id, active_model="mrp.production"
        ).default_get(["mo_id"])
        wizard = wizard_obj.create(wizard_vals)
        wizard.action_done()
        self.assertEqual(len(production.move_raw_ids), 2)

        production.action_assign()
        self.assertEqual(self.subproduct_1_1.virtual_available, 0)
        self.assertEqual(self.subproduct_2_1.virtual_available, 0)
        self.assertEqual(production.reservation_state, "assigned")
        production_form = Form(production)
        production_form.qty_producing = 3.0
        production = production_form.save()
        production.button_mark_done()
        self.assertEqual(len(production), 1)
        self.assertEqual(
            production.move_raw_ids.filtered(
                lambda x: x.product_id == self.subproduct_1_1
            ).quantity_done,
            16 * 3,
        )
        self.assertEqual(
            production.move_raw_ids.mapped("product_uom_qty"), [16 * 3, 8 * 3]
        )
        self.assertEqual(
            production.move_raw_ids.mapped("quantity_done"), [16 * 3, 8 * 3]
        )
        production.button_mark_done()
        self.assertFalse(production.reservation_state)
        self.assertEqual(self.top_product.qty_available, 3)
