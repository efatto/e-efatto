from odoo import api, fields, models


class MrpWorkorder(models.Model):
    _inherit = ['mrp.workorder', 'mail.thread', 'mail.activity.mixin']
    _name = 'mrp.workorder'

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Assigned user',
        index=True,
    )
    activity_date_start = fields.Datetime(
        compute="_compute_dates",
        store=True,
    )
    activity_date_end = fields.Datetime(
        compute="_compute_dates",
        store=True,
    )

    @api.multi
    @api.depends('activity_ids.date_start', 'activity_ids.date_end')
    def _compute_dates(self):
        for workorder in self:
            workorder.activity_date_start = min(
                workorder.mapped("activity_ids.date_start") or [False])
            workorder.activity_date_end = max(
                workorder.mapped("activity_ids.date_end") or [False])

    @api.model
    def create(self, vals_list):
        workorder = super().create(vals_list)
        activity_ids = workorder.activity_ids.filtered(
            lambda x: x.is_resource_planner
        )
        if not activity_ids:
            self.env['mail.activity'].create_planner_activity(
                workorder,
                workorder.user_id or workorder.production_id.user_id)
        return workorder

    @api.multi
    def write(self, values):
        res = super().write(values)
        if not self.env.context.get('bypass_resource_planner'):
            for workorder in self:
                # search as activities could be not linked at the moment of write
                activity_ids = self.env['mail.activity'].search([
                    ('res_model', '=', workorder._name),
                    ('res_id', '=', workorder.id),
                ])
                if activity_ids:
                    if any(x in values for x in [
                        'date_planned_start',
                        'date_planned_finished',
                        'user_id',
                        'parent_id',
                        'name'
                    ]):
                        activity_ids._compute_planner()
        return res

    @api.multi
    def record_production(self):
        res = super().record_production()
        if self.state == 'done':
            activity_ids = self.activity_ids.filtered(lambda x: x.is_resource_planner)
            activity_ids.action_done()
        return res
