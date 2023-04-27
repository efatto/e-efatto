from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    workcenter_id = fields.Many2one(
        comodel_name='mrp.workcenter',
        index=True,
    )
    color = fields.Integer(related='project_id.color')

    @api.model
    def create(self, vals_list):
        task = super().create(vals_list)
        activity_ids = task.activity_ids.filtered(
            lambda x: x.is_resource_planner
        )
        if not activity_ids and vals_list.get("user_id", False):
            # create only when a user directly create task
            self.env['mail.activity'].create_planner_activity(
                task,
                task.workcenter_id.user_id or
                task.user_id or
                task.project_id.user_id)
        return task

    @api.multi
    def write(self, values):
        res = super().write(values)
        if not self.env.context.get('bypass_resource_planner'):
            for task in self:
                activity_ids = task.activity_ids.filtered(
                    lambda x: x.is_resource_planner
                )
                if activity_ids:
                    if any(x in values for x in [
                        'date_start',
                        'date_end',
                        'user_id',
                        'parent_id',
                        'name',
                        'workcenter_id'
                    ]):
                        activity_ids._compute_planner()
        return res
