from . import colorscale
from odoo import api, fields, models, _


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    active = fields.Boolean(default=True)
    is_resource_planner = fields.Boolean(
        related='activity_type_id.is_resource_planner',
        store=True,
    )
    date_start = fields.Datetime(
        compute='_compute_planner',
        store=True,
    )
    date_end = fields.Datetime(
        compute='_compute_planner',
        store=True,
    )
    parent_id = fields.Many2one(
        comodel_name='mail.activity',
        string="Parent Activity",
        ondelete="cascade",
        index=True,
    )
    workcenter_id = fields.Many2one(
        comodel_name='mrp.workcenter',
        index=True,
    )
    color_active = fields.Char(
        compute='_compute_planner',
        store=True,
    )

    def action_activity_duplicate(self):
        self.ensure_one()
        new_activity = self.copy()
        return {
            'name': _('Schedule duplicated Activity'),
            'context': {},
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.activity',
            'res_id': new_activity.id,
            'views': [(False, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def write(self, values):
        res = super().write(values)

        for activity in self:
            if activity.is_resource_planner:
                if any(x in values for x in [
                    'date_start',
                    'date_end',
                    'user_id',
                    'parent_id',
                    'summary',
                    'workcenter_id'
                ]):
                    res_object = self.env[activity.res_model].browse(
                        activity.res_id)
                    vals = {}
                    if 'user_id' in values:
                        vals.update({'user_id': values['user_id']})
                    if 'parent_id' in values:
                        vals.update({'parent_id': values['parent_id']})
                    if 'summary' in values:
                        vals.update({
                            'name': values['summary']
                        })
                    if 'workcenter_id' in values:
                        vals.update({'workcenter_id': values['workcenter_id']})
                    if activity.res_model == 'mrp.workorder':
                        if 'date_start' in values:
                            vals.update({
                                'date_planned_start': values['date_start']
                            })
                        if 'date_end' in values:
                            vals.update({
                                'date_planned_finished': values['date_end']
                            })
                    elif activity.res_model == 'project.task':
                        if 'date_start' in values:
                            vals.update({
                                'date_start': values['date_start']
                            })
                        if 'date_end' in values:
                            vals.update({
                                'date_end': values['date_end']
                            })
                    res_object.with_context(
                        bypass_resource_planner=True
                    ).write(vals)
                    if 'name' in vals:
                        # force recompute of res_name as it is not present in depends
                        activity._compute_res_name()
        return res

    @api.model
    def create_planner_activity(self, object, user_id):
        res_model = self.env['ir.model'].search([
            ('model', '=', object._name)
        ])
        activity_type = self.env['mail.activity.type'].search([
            ('is_resource_planner', '=', True),
            ('res_model_id', '=', res_model.id),
        ])
        vals = {
            'activity_type_id': activity_type.id,
            'res_model_id': res_model.id,
            'res_id': object.id,
            'summary': object.name,
            'partner_id': object.partner_id.id,
            'commercial_partner_id': object.partner_id.commercial_partner_id.id,
            'parent_id': object.parent_id.id,
            'user_id': user_id.id,
            'is_resource_planner': True,
            'color': object.color_active,
            'workcenter_id': object.workcenter_id.id if object._name == 'mrp.workorder'
            else self.env.ref(
                'mail_activity_timeline.mail_activity_project_mrp_workcenter').id,
            'team_id': False,  # to excludes problem of users not part of the team
            # if needed, add a check to ensure that user is part of the team
        }
        res = self.create(vals)
        res._compute_planner()
        return res

    @staticmethod
    def get_color(res_object, color):
        if res_object._name == 'mrp.workorder':
            if res_object.state in ['done', 'cancel']:
                color = colorscale.colorscale(color, .5)
        elif res_object._name == 'project.task':
            color = hex(color)
            if res_object.stage_id.state in ['done', 'cancelled']:
                color = colorscale.colorscale(color, .5)
        return color

    @api.multi
    @api.depends('res_model', 'res_id')
    def _compute_planner(self):
        # for this compute @api.depends is only partial possible, as dependants fields
        # (like dates) are not linkable directly, only res_model and res_id
        for activity in self:
            if activity.res_model and activity.res_id and activity.res_model in [
                'mrp.workorder', 'project.task'
            ]:
                res_object = self.env[activity.res_model].browse(activity.res_id)
                if activity.res_model == 'mrp.workorder':
                    activity.date_start = res_object.date_planned_start
                    activity.date_end = res_object.date_planned_finished
                elif activity.res_model == 'project.task':
                    activity.date_start = res_object.date_start
                    activity.date_end = res_object.date_end
                if activity.date_end:
                    activity.date_deadline = fields.Date.to_date(activity.date_end)
                if res_object.parent_id:
                    activity.parent_id = res_object.parent_id.activity_ids.filtered(
                        lambda x: x.is_resource_planner
                    )
                if res_object.user_id:
                    activity.user_id = res_object.user_id
                if res_object.workcenter_id:
                    activity.workcenter_id = res_object.workcenter_id
                if res_object.color:
                    activity.color_active = self.get_color(res_object, res_object.color)
            else:
                activity.date_start = False
                activity.date_end = False
                activity.color_active = False
