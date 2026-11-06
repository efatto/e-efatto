from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestMrpProductionSet(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.workcenter_left = cls.env["mrp.workcenter"].create(
            {
                "name": "Set Left Workcenter",
                "mrp_set_position": "left",
            }
        )
        cls.workcenter_right = cls.env["mrp.workcenter"].create(
            {
                "name": "Set Right Workcenter",
                "mrp_set_position": "right",
            }
        )
        cls.workcenter_standard = cls.env["mrp.workcenter"].create(
            {"name": "Set Standard Workcenter"}
        )
        cls.workcenter_left.alternative_workcenter_ids = cls.workcenter_right
        cls.workcenter_right.alternative_workcenter_ids = cls.workcenter_left
        cls.component = cls._create_product("Set Component")
        cls.component_2 = cls._create_product("Set Component 2")
        cls.product_left = cls._create_product("Set Finished Left")
        cls.product_right = cls._create_product("Set Finished Right")
        cls.product_other = cls._create_product("Set Finished Other")
        cls.bom_left = cls._create_bom(cls.product_left, cls.workcenter_left)
        cls.bom_right = cls._create_bom(cls.product_right, cls.workcenter_right)
        cls.bom_other = cls._create_bom(
            cls.product_other, cls.workcenter_left, component=cls.component_2
        )
        cls.production_left = cls._create_production(cls.product_left, cls.bom_left)
        cls.production_right = cls._create_production(cls.product_right, cls.bom_right)
        cls.production_other = cls._create_production(cls.product_other, cls.bom_other)

    @classmethod
    def _create_product(cls, name):
        return cls.env["product.product"].create(
            {
                "name": name,
                "type": "consu",
                "is_storable": True,
            }
        )

    @classmethod
    def _create_bom(cls, product, workcenter, component=None, operations=True):
        vals = {
            "product_tmpl_id": product.product_tmpl_id.id,
            "product_qty": 1,
            "bom_line_ids": [
                Command.create(
                    {
                        "product_id": (component or cls.component).id,
                        "product_qty": 1,
                    }
                )
            ],
        }
        if operations:
            vals["operation_ids"] = [
                Command.create(
                    {
                        "name": f"Operation {product.name}",
                        "workcenter_id": workcenter.id,
                        "time_mode": "manual",
                        "time_cycle_manual": 60,
                        "sequence": 1,
                    }
                )
            ]
        return cls.env["mrp.bom"].create(vals)

    @classmethod
    def _create_standard_operations_bom(cls):
        """Left workcenter operation + operation on a workcenter without position."""
        bom = cls._create_bom(cls.product_left, cls.workcenter_left, operations=False)
        bom.operation_ids = [
            Command.create(
                {
                    "name": "Operation on set position",
                    "workcenter_id": cls.workcenter_left.id,
                    "time_mode": "manual",
                    "time_cycle_manual": 60,
                    "sequence": 1,
                }
            ),
            Command.create(
                {
                    "name": "Standard operation",
                    "workcenter_id": cls.workcenter_standard.id,
                    "time_mode": "manual",
                    "time_cycle_manual": 30,
                    "sequence": 2,
                }
            ),
        ]
        return bom

    @classmethod
    def _create_production(cls, product, bom):
        production = cls.env["mrp.production"].create(
            {
                "product_id": product.id,
                "bom_id": bom.id,
                "product_qty": 1,
            }
        )
        production.action_confirm()
        return production

    def _create_production_set(self, left=None, right=None, split=False):
        return self.env["mrp.production.set"].create(
            {
                "production_left_id": (left or self.production_left).id,
                "production_right_id": (right or self.production_right).id,
                "split_production": split,
            }
        )

    def test_00_compatible_for_set(self):
        self.assertTrue(self.production_left.is_compatible_for_set)
        self.assertEqual(len(self.production_left.move_raw_ids), 1)
        self.assertTrue(self.production_left.workorder_ids)
        # more than one component: not compatible
        bom = self._create_bom(
            self.product_left, self.workcenter_left, operations=False
        )
        bom.bom_line_ids = [
            Command.create({"product_id": self.component_2.id, "product_qty": 1})
        ]
        production = self.env["mrp.production"].create(
            {
                "product_id": self.product_left.id,
                "bom_id": bom.id,
                "product_qty": 1,
            }
        )
        self.assertEqual(len(production.move_raw_ids), 2)
        self.assertFalse(production.is_compatible_for_set)

    def test_01_production_set_computes(self):
        production_set = self._create_production_set()
        self.assertEqual(
            production_set.name,
            f"{self.production_left.name} - {self.production_right.name}",
        )
        self.assertEqual(production_set.state, self.production_left.state)
        self.assertTrue(self.production_left.has_production_set)
        self.assertTrue(self.production_right.has_production_set)
        self.assertEqual(production_set.move_raw_product_id, self.component)
        self.assertEqual(
            production_set.left_finished_product_id, self.production_left.product_id
        )
        self.assertEqual(
            production_set.right_finished_product_id, self.production_right.product_id
        )
        self.assertEqual(production_set.workcenter_left_ids, self.workcenter_left)
        self.assertEqual(production_set.workcenter_right_ids, self.workcenter_right)
        self.assertIn(
            self.production_right, production_set.compatible_mrp_production_ids
        )

    def test_02_display_name(self):
        self.assertEqual(self.production_left.display_name, self.production_left.name)
        display_name = self.production_left.with_context(
            mrp_production_set_display_name=True
        ).display_name
        self.assertEqual(
            display_name,
            f"{self.production_left.name} - {self.production_left.product_id.name}",
        )

    def test_03_get_workcenter_id(self):
        # outside a production set the workorder can use workcenter and alternatives
        self.assertEqual(
            set(self.production_left.workorder_ids._get_workcenter_id().ids),
            {self.workcenter_left.id, self.workcenter_right.id},
        )
        self._create_production_set()
        # the workorder of the left production can only use the left workcenter
        self.assertEqual(
            self.production_left.workorder_ids._get_workcenter_id(),
            self.workcenter_left,
        )
        self.assertEqual(
            self.production_right.workorder_ids._get_workcenter_id(),
            self.workcenter_right,
        )
        # a workorder not using a set position keeps its standard workcenter
        production = self._create_production(
            self.product_left, self._create_standard_operations_bom()
        )
        self._create_production_set(left=production, right=self.production_right)
        self.assertEqual(
            production.workorder_ids.filtered(
                lambda wo: wo.workcenter_id == self.workcenter_standard
            )._get_workcenter_id(),
            self.workcenter_standard,
        )
        self.assertEqual(
            production.workorder_ids.filtered(
                lambda wo: wo.workcenter_id == self.workcenter_left
            )._get_workcenter_id(),
            self.workcenter_left,
        )

    def test_04_split_production(self):
        form = Form(self.env["mrp.production.set"])
        form.production_left_id = self.production_left
        form.production_right_id = self.production_left
        production_set = form.save()
        self.assertTrue(production_set.split_production)
        self.assertEqual(production_set.state, self.production_left.state)
        # checking split production sets the right production to the left one
        form = Form(self.env["mrp.production.set"])
        form.production_left_id = self.production_left
        form.split_production = True
        self.assertEqual(form.production_right_id, self.production_left)

    def test_05_button_plan_split_production(self):
        production_set = self._create_production_set(
            left=self.production_left, right=self.production_left, split=True
        )
        self.assertEqual(
            production_set.production_left_id.workorder_ids.duration_expected, 60
        )
        production_set.button_plan()
        workorders = self.production_left.workorder_ids
        self.assertEqual(len(workorders), 2, "the workorder must be split in two")
        self.assertEqual(
            set(workorders.mapped("workcenter_id").ids),
            {self.workcenter_left.id, self.workcenter_right.id},
        )
        self.assertEqual(len(workorders.operation_id), 1)
        self.assertEqual(set(workorders.mapped("duration_expected")), {30})
        self.assertTrue(all(workorders.mapped("date_start")))
        self.assertTrue(production_set.is_planned)
        production_set.button_unplan()
        self.assertFalse(production_set.is_planned)

    def test_06_update_qty_producing(self):
        production_set = self._create_production_set()
        production_set.qty_producing_left = 1
        production_set.qty_producing_right = 1
        production_set.button_update_qty_producing()
        self.assertEqual(self.production_left.qty_producing, 1)
        self.assertEqual(self.production_right.qty_producing, 1)
        # the component quantities follow the producing quantity (onchange logic)
        self.assertEqual(self.production_left.move_raw_ids.quantity, 1)
        self.assertEqual(self.production_right.move_raw_ids.quantity, 1)

    def test_07_check_same_component(self):
        with self.assertRaises(ValidationError):
            self._create_production_set(
                left=self.production_left, right=self.production_other
            )

    def test_08_check_bom_operations(self):
        # only one operation per set position is allowed in a bill of materials
        with self.assertRaises(ValidationError):
            self.env["mrp.bom"].create(
                {
                    "product_tmpl_id": self.product_left.product_tmpl_id.id,
                    "product_qty": 1,
                    "operation_ids": [
                        Command.create(
                            {
                                "name": "Left operation",
                                "workcenter_id": self.workcenter_left.id,
                            }
                        ),
                        Command.create(
                            {
                                "name": "Left operation 2",
                                "workcenter_id": self.workcenter_left.id,
                            }
                        ),
                    ],
                }
            )

    def test_09_check_alternative_workcenter(self):
        workcenter = self.env["mrp.workcenter"].create(
            {"name": "Set Left Workcenter 2", "mrp_set_position": "left"}
        )
        with self.assertRaises(ValidationError):
            workcenter.alternative_workcenter_ids = (
                self.workcenter_left | self.workcenter_right
            )

    def test_10_plan_production_set_with_standard_operation(self):
        # a production of a set can have other operations on standard workcenters:
        # they must still be planned
        production = self._create_production(
            self.product_left, self._create_standard_operations_bom()
        )
        production_set = self._create_production_set(
            left=production, right=self.production_right
        )
        production_set.button_plan()
        self.assertTrue(production_set.is_planned)
        self.assertEqual(len(production.workorder_ids), 2)
        self.assertEqual(
            set(production.workorder_ids.mapped("workcenter_id").ids),
            {self.workcenter_left.id, self.workcenter_standard.id},
        )
        self.assertTrue(all(production.workorder_ids.mapped("date_start")))
        self.assertTrue(all(self.production_right.workorder_ids.mapped("date_start")))
