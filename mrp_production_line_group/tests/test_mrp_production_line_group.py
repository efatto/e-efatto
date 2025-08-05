from odoo.tests import Form

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData


class TestProductionGroupLine(TestProductionData):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def _get_production_vals(self):
        return {
            "product_id": self.top_product.id,
            "product_qty": 1,
            "product_uom_id": self.uom_unit.id,
            "bom_id": self.main_bom.id,
        }

    def test_mo_by_product(self):
        self._update_product_qty(self.subproduct_1_1, 16 * 3)
        self._update_product_qty(self.subproduct_2_1, 8 * 3)
        self.production = self.production_model.create(self._get_production_vals())
        self.production.action_assign()
        self.assertEquals(self.subproduct_1_1.virtual_available, 16 * 2)

        wizard_obj = self.env["production.group.line.wizard"]
        wizard_vals = wizard_obj.with_context(
            active_id=self.production.id, active_model="mrp.production"
        ).default_get(["mo_id"])
        wizard = wizard_obj.create(wizard_vals)
        wizard.action_done()
        self.assertEqual(len(self.production), 1)
        self.assertEqual(len(self.production.move_raw_ids), 2)
        # 5*2=10 in sub1, 2*3=6 in sub2
        self.assertEqual(
            self.production.move_raw_ids.filtered(
                lambda x: x.product_id == self.subproduct_1_1
            ).product_uom_qty,
            16,
        )

        # check change.production.qty is callable, but it split lines again
        change_qty_wizard = self.env["change.production.qty"].create(
            {
                "mo_id": self.production.id,
                "product_qty": 3.0,
            }
        )
        change_qty_wizard.change_prod_qty()
        wizard_obj = self.env["production.group.line.wizard"]
        wizard_vals = wizard_obj.with_context(
            active_id=self.production.id, active_model="mrp.production"
        ).default_get(["mo_id"])
        wizard = wizard_obj.create(wizard_vals)
        wizard.action_done()

        self.production.action_assign()
        self.assertEqual(self.subproduct_1_1.virtual_available, 0)
        self.assertEqual(self.subproduct_2_1.virtual_available, 0)
        self.assertEqual(self.production.reservation_state, "waiting")
        production_form = Form(self.production)
        production_form.qty_producing = 3.0
        production = production_form.save()
        production.button_mark_done()
        self.assertEqual(len(production), 1)
        self.assertEqual(
            production.move_raw_ids.filtered(
                lambda x: x.product_id == self.subproduct_1_1
            ).unit_factor,
            16,
        )
        self.assertEqual(
            production.move_raw_ids.mapped("product_uom_qty"), [16 * 3, 8 * 3]
        )
        self.assertEqual(
            production.move_raw_ids.mapped("quantity_done"), [16 * 3, 8 * 3]
        )
        production.button_mark_done()
        self.assertEqual(production.reservation_state, "assigned")
        self.assertEquals(self.top_product.qty_available, 3)
