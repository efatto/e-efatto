from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestConnectorWmsWhsSetGlue(TransactionCase):
    """Glue between connector_whs and mrp_production_set, without the WMS server.

    ``button_send_to_whs`` only creates ``hyddemo.whs.liste`` rows, so a dummy
    ``base.external.dbsource`` on the stock location is enough: no MSSQL
    connection is needed (unlike ``tests/test_connector_wms_whs_set.py``).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref("stock.stock_location_stock")  # noqa
        cls.env["base.external.dbsource"].create(
            {
                "name": "WMS test source",
                "connector": "mssql",
                "conn_string": "mssql+pymssql://user:password@wms/whs",
                "location_id": cls.stock_location.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.workcenter_left = cls.env["mrp.workcenter"].create(
            {
                "name": "Set workcenter left",
                "mrp_set_position": "left",
                "default_capacity": 1,
                "time_start": 10,
                "time_stop": 5,
                "time_efficiency": 80,
                "costs_hour": 23.0,
            }
        )
        cls.workcenter_right = cls.env["mrp.workcenter"].create(
            {
                "name": "Set workcenter right",
                "mrp_set_position": "right",
                "default_capacity": 1,
                "time_start": 10,
                "time_stop": 5,
                "time_efficiency": 80,
                "costs_hour": 23.0,
            }
        )
        cls.workcenter_left.alternative_workcenter_ids = cls.workcenter_right.ids
        cls.component = cls.env["product.product"].create(
            {
                "name": "Set component",
                "default_code": "SET_COMPONENT",
                "type": "consu",
                "is_storable": True,
            }
        )

    def _create_finished_product(self, code, workcenter):
        product = self.env["product.product"].create(
            {
                "name": code,
                "default_code": code,
                "type": "consu",
                "is_storable": True,
            }
        )
        self.env["mrp.bom"].create(
            {
                "product_tmpl_id": product.product_tmpl_id.id,
                "product_qty": 10.0,
                "type": "normal",
                "bom_line_ids": [
                    Command.create(
                        {
                            "product_id": self.component.id,
                            "product_qty": 10.0,
                        }
                    )
                ],
                "operation_ids": [
                    Command.create(
                        {
                            "name": f"Operation {code}",
                            "workcenter_id": workcenter.id,
                            "time_cycle_manual": 10.0,
                        }
                    )
                ],
            }
        )
        return product

    def _create_production(self, code, workcenter):
        product = self._create_finished_product(code, workcenter)
        production = self.env["mrp.production"].create(
            {
                "product_id": product.id,
                "bom_id": product.bom_ids[0].id,
                "product_qty": 10.0,
            }
        )
        production.action_confirm()
        self.assertEqual(production.workorder_ids.mapped("workcenter_id"), workcenter)
        self.assertTrue(production.is_compatible_for_set)
        return production

    def _create_production_set(self, left, right):
        production_set = self.env["mrp.production.set"].create(
            {
                "production_left_id": left.id,
                "production_right_id": right.id,
            }
        )
        self.assertFalse(production_set.split_production)
        return production_set

    def test_10_not_split_set_lists(self):
        # left and right productions share the same num_lista, riga 1 and 2,
        # and the tipo of a production set is always 12 (lavorazione isola)
        left = self._create_production("SET LEFT", self.workcenter_left)
        right = self._create_production("SET RIGHT", self.workcenter_right)
        production_set = self._create_production_set(left, right)
        production_set.write({"qty_producing_left": 5.0, "qty_producing_right": 5.0})
        production_set.button_update_qty_producing()
        self.assertEqual(production_set.state, "progress")
        production_set.button_send_to_whs()
        left_lists = left.move_raw_ids.whs_list_ids
        right_lists = right.move_raw_ids.whs_list_ids
        self.assertEqual(len(left_lists), 1)
        self.assertEqual(len(right_lists), 1)
        self.assertEqual(left_lists.num_lista, right_lists.num_lista)
        self.assertEqual(left_lists.riga, 1)
        self.assertEqual(right_lists.riga, 2)
        self.assertEqual(
            set((left | right).move_raw_ids.whs_list_ids.mapped("tipo")), {"12"}
        )
        self.assertTrue(production_set.sent_to_whs)
        self.assertTrue(left.sent_to_whs)
        self.assertTrue(right.sent_to_whs)

    def test_11_split_set_qty(self):
        # a split production is the same production on both sides: one whs list
        # per row, each with the quantity producing of its side
        production = self._create_production("SET SPLIT", self.workcenter_left)
        production_set = self.env["mrp.production.set"].create(
            {
                "production_left_id": production.id,
                "production_right_id": production.id,
            }
        )
        production_set.write(
            {
                "split_production": True,
                "qty_producing_left": 3.0,
                "qty_producing_right": 2.0,
            }
        )
        production_set.button_update_qty_producing()
        self.assertEqual(production.qty_producing, 5.0)
        production_set.button_send_to_whs()
        lists = production.move_raw_ids.whs_list_ids.sorted("riga")
        self.assertEqual(lists.mapped("riga"), [1, 2])
        self.assertEqual(lists.mapped("qta"), [3.0, 2.0])
        self.assertEqual(len(set(lists.mapped("num_lista"))), 1)
        self.assertEqual(set(lists.mapped("tipo")), {"12"})
        self.assertTrue(production_set.sent_to_whs)

    def test_12_wrong_left_workcenter(self):
        left = self._create_production("SET LEFT WC", self.workcenter_left)
        right = self._create_production("SET RIGHT WC", self.workcenter_right)
        production_set = self._create_production_set(left, right)
        left.workorder_ids.workcenter_id = self.workcenter_right
        with self.assertRaises(ValidationError):
            production_set.button_send_to_whs()

    def test_13_wrong_right_workcenter(self):
        left = self._create_production("SET LEFT WC2", self.workcenter_left)
        right = self._create_production("SET RIGHT WC2", self.workcenter_right)
        production_set = self._create_production_set(left, right)
        right.workorder_ids.workcenter_id = self.workcenter_left
        with self.assertRaises(ValidationError):
            production_set.button_send_to_whs()

    def test_14_left_riga_two_guard(self):
        # a not split production that was split and then unsplit still has the
        # riga #2 whs list: sending it to WHS must be blocked
        left = self._create_production("SET RIGA LEFT", self.workcenter_left)
        right = self._create_production("SET RIGA RIGHT", self.workcenter_right)
        production_set = self._create_production_set(left, right)
        self.env["hyddemo.whs.liste"].create(
            {
                "num_lista": "TEST-OLD",
                "riga": 2,
                "stato": "1",
                "tipo": "12",
                "riferimento": left.name,
                "product_id": self.component.id,
                "qta": 1.0,
                "qtamov": 1.0,
                "move_id": left.move_raw_ids[0].id,
                "tipo_mov": "mrpout",
            }
        )
        with self.assertRaises(ValidationError):
            production_set.button_send_to_whs()
