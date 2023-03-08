# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, api


class MrpWorkOrder(models.Model):
    _inherit = "mrp.workorder"
    _order = "sequence"
    # set order on sequence for user better experience, as workorder could not follow
    # default id sequence


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def _generate_workorders(self, exploded_boms):
        workorders = super()._generate_workorders(exploded_boms)
        # recreate sequence: first do the components workorders, then the final products
        finished_workorders = workorders.filtered(
            lambda x: x.operation_id.routing_id == self.routing_id
        )
        last_workorder = workorders.filtered(
            lambda y: y.move_raw_ids
        )
        component_workorders = workorders - finished_workorders
        if finished_workorders:
            # Assign moves to last finished workorders
            last_workorder.move_raw_ids.write({
                'workorder_id': finished_workorders[-1].id})
            last_workorder.move_raw_ids.mapped('move_line_ids').write({
                'workorder_id': finished_workorders[-1].id})
            original_one = False
            i = 0
            component_original_one = False
            if component_workorders:
                for workorder in component_workorders:
                    i += 1
                    workorder.sequence = i
                    if original_one:
                        component_workorders[-1].next_work_order_id = original_one
                    original_one = component_workorders[0]
                component_original_one = component_workorders[-1]
            for finished_workorder in finished_workorders:
                i += 1
                finished_workorder.sequence = i
                if component_original_one:
                    component_original_one.next_work_order_id = finished_workorders[0]
                    original_one = component_original_one
                    component_original_one = False
                if original_one:
                    finished_workorders[-1].next_work_order_id = original_one
                original_one = component_workorders and component_workorders[0] or \
                    finished_workorders[0]
            # last work order cannot have a next work order
            finished_workorders[-1].next_work_order_id = False
        return workorders
