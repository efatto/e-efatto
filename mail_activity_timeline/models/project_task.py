from odoo import api, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.model
    def create(self, vals_list):
        task = super().create(vals_list)
        activity_ids = task.activity_ids.filtered(
            lambda x: x.is_resource_planner
        )
        if not activity_ids:
            self.env['mail.activity'].create_planner_activity(
                task,
                task.user_id or task.project_id.user_id)
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
                        'name'
                    ]):
                        activity_ids._compute_planner()
        return res
