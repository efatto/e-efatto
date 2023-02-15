from odoo import api, fields, models


class MrpWorkorder(models.Model):
    _inherit = ['mrp.workorder', 'mail.thread', 'mail.activity.mixin']
    _name = 'mrp.workorder'

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Assigned user',
        index=True,
    )

    @api.model
    def create(self, vals_list):
        workorder = super().create(vals_list)
        activitity_ids = workorder.activity_ids.filtered(
            lambda x: x.is_resource_planner
        )
        if not activitity_ids:
            self.env['mail.activity'].create_planner_activity(workorder)
        return workorder

    @api.multi
    def write(self, values):
        res = super().write(values)
        if not self.env.context.get('bypass_resource_planner'):
            for workorder in self:
                activitity_ids = workorder.activity_ids.filtered(
                    lambda x: x.is_resource_planner
                )
                if activitity_ids:
                    if any(x in values for x in [
                        'date_planned_start',
                        'date_planned_finished',
                        'user_id',
                        'parent_id'
                    ]):
                        activitity_ids._compute_dates()
        return res
