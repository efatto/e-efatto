from odoo.tests import Form

from odoo.addons.mrp_production_demo.tests.common_data import TestProductionData
from odoo.tools import mute_logger


class TestMrpBomEvaluation(TestProductionData):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service_product = cls.env["product.product"].create({
            "name": "Service product",
            "type": "service",
            "uom_id": cls.env.ref("uom.product_uom_hour").id,
            "uom_po_id": cls.env.ref("uom.product_uom_hour").id,
            "service_tracking": "task_new_project",
        })
        cls.partner = cls.env.ref('base.res_partner_2')
        cls.partner.customer = True
        cls.main_bom.write({
            "bom_line_ids": [
                (0, 0, {
                    "product_id": cls.service_product.id,
                    "product_qty": 5,
                    "product_uom_id": cls.service_product.uom_id.id,
                })
            ]
        })

    def test_01_create_task_from_mo(self):
        order_form = Form(self.env['sale.order'])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as order_line:
            order_line.product_id = self.top_product
            order_line.product_uom_qty = 1
            order_line.price_unit = 100
        order1 = order_form.save()
        order1.action_confirm()
        if self.env["ir.module.module"].search([
                ("name", "=", "sale_order_approved_customer"),
                ("state", "=", "installed")]):
            order1.action_confirm()
        self.assertEqual(order1.state, 'sale')
        with mute_logger('odoo.addons.stock.models.procurement'):
            self.procurement_model.run_scheduler()
        self.production = self.env['mrp.production'].search(
            [('origin', '=', order1.name)])
        self.assertTrue(self.production)
        self.production.action_assign()
        service_lines = order1.order_line.filtered(
            lambda x: x.product_id == self.service_product
        )
        self.assertEqual(len(service_lines), 1)
        self.assertTrue(order1.tasks_ids)
        self.assertEqual(len(order1.tasks_ids), 1)
        task = order1.tasks_ids[0]
        self.assertEqual(task.planned_hours, service_lines.bom_line_id.product_qty)
        self.assertEqual(service_lines.product_uom_qty,
                         service_lines.bom_line_id.product_qty)
