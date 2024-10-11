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
        string="Work Center",
        comodel_name='mrp.workcenter',
        index=True,
    )
    color_active = fields.Char(
        compute='_compute_planner',
        store=True,
    )
    info = fields.Char(
        compute='_compute_planner',
        store=True,
    )
    origin_res_id = fields.Integer(
        compute='_compute_planner',
        store=True,
    )
    mail_activity_origin_id = fields.Many2one(
        comodel_name='mail.activity.origin',
        string='Origin',
    )

    def _get_mail_activity_origin(self):
        self.ensure_one()
        res_object = self.env[self.res_model].browse(self.res_id)
        name = self.res_name
        if self.res_model == 'mrp.workorder':
            name = res_object.production_id.name
        elif self.res_model == 'project.task':
            if res_object.project_id.sale_order_id:
                name = res_object.project_id.sale_order_id.name
            else:
                if ':' in res_object.project_id.name:
                    name = res_object.project_id.name.split(':')[0]
                else:
                    name = res_object.project_id.name
        mail_activity_origin_ids = self.env['mail.activity.origin'].search([
            ('name', '=', name),
        ], limit=1)
        if mail_activity_origin_ids:
            return mail_activity_origin_ids[0]
        mail_activity_origin_id = self.env['mail.activity.origin'].create(
            [{
                'name': name,
            }]
        )
        return mail_activity_origin_id

    def toggle_active(self):
        res = super().toggle_active()
        for activity in self:
            activity.done = not bool(activity.active)
        return res

    def action_activity_duplicate(self):
        self.ensure_one()
        new_activity = self.copy(default={
            'parent_id': self.id,
        })
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
                    'workcenter_id',
                    'done',
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
                        # if 'state' in values:  # TODO questo campo c'è ma potrebbe non
                        #     # essere interessante
                        #     # updata current write values
                        #     activity.color_active = self.get_color(
                        #         res_object,
                        #         res_object.color,
                        #     )
                    elif activity.res_model == 'project.task':
                        if 'date_start' in values:
                            vals.update({
                                'date_start': values['date_start']
                            })
                        if 'date_end' in values:
                            vals.update({
                                'date_end': values['date_end']
                            })
                        if 'done' in values:
                            # updata current write values
                            activity.color_active = self.get_color(
                                    activity,
                                    res_object.project_id.activity_color,
                            )
                    res_object.with_context(
                        bypass_resource_planner=True
                    ).write(vals)
                    if 'name' in vals:
                        # force recompute of res_name as it is not present in depends
                        activity._compute_res_name()
                if not activity.mail_activity_origin_id:
                    mail_activity_origin_id = activity._get_mail_activity_origin()
                    activity.mail_activity_origin_id = mail_activity_origin_id
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
            'color_active': object.color,
            'workcenter_id': object.workcenter_id.id if object._name == 'mrp.workorder'
            else self.env.ref(
                'mail_activity_timeline.mail_activity_project_mrp_workcenter').id,
            'team_id': False,  # to excludes problem of users not part of the team
            # if needed, add a check to ensure that user is part of the team
            # Do not remove: this is requested as team is auto-assigned
        }
        res = self.create(vals)
        if not res.mail_activity_origin_id:
            mail_activity_origin_id = res._get_mail_activity_origin()
            res.mail_activity_origin_id = mail_activity_origin_id
        res._compute_planner()
        return res

    @staticmethod
    def get_color(res_object, color):
        if res_object._name == 'mrp.workorder':
            if res_object.state in ['done', 'cancel']:
                color = colorscale.colorscale(color, .5)
        elif res_object._name == 'project.task':
            # color = hex(color)  # perché c'era questo?
            # per trasformare da colore numerico a testo, ma non va
            if res_object.stage_id.state in ['done', 'cancelled']:
                color = colorscale.colorscale(color, .5)
        elif res_object._name == "mail.activity":
            if res_object.done:
                color = colorscale.colorscale(color, .5)
        return color

    @api.multi
    @api.depends('res_model', 'res_id')
    def _compute_planner(self):
        # for this compute @api.depends is only partial possible, as dependants fields
        # (like dates) are not linkable directly, only res_model and res_id
        for activity in self:
            vals = {}
            if activity.res_model and activity.res_id and activity.res_model in [
                'mrp.workorder', 'project.task'
            ]:
                res_object = self.env[activity.res_model].browse(activity.res_id)
                if activity.res_model == 'mrp.workorder':
                    vals.update({
                        'date_start': res_object.date_planned_start,
                        'date_end': res_object.date_planned_finished,
                        'info': "%s - %s - %s - %s" % (
                            activity.workcenter_id.name,
                            res_object.production_id.name,
                            res_object.name,
                            res_object.origin or ''),
                        'origin_res_id': res_object.production_id.id,
                    })
                elif activity.res_model == 'project.task':
                    vals.update({
                        'date_start': res_object.date_start,
                        'date_end': res_object.date_end,
                        'info': "%s - %s - %s - %s" % (
                            activity.workcenter_id.name,
                            res_object.project_id.name,
                            res_object.name,
                            res_object.sale_line_id.order_id.origin or ''),
                        'origin_res_id': res_object.project_id.id,
                    })
                if vals.get('date_end'):
                    vals.update({
                        'date_deadline': fields.Date.to_date(vals['date_end']),
                    })
                if res_object.parent_id.activity_ids:
                    vals.update({
                        'parent_id': res_object.parent_id.activity_ids.filtered(
                            lambda x: x.is_resource_planner)[0].id,
                    })
                if res_object.user_id:
                    vals.update({
                        'user_id': res_object.user_id.id,
                    })
                if res_object.workcenter_id:
                    vals.update({
                        'workcenter_id': res_object.workcenter_id.id,
                    })
                if res_object.color:
                    if res_object.project_id and res_object.project_id.activity_color:
                        vals.update({
                            'color_active': self.get_color(
                                activity,
                                res_object.project_id.activity_color),
                        })
                    else:
                        vals.update({
                            'color_active': self.get_color(res_object, res_object.color),
                        })
            for val in vals:
                if vals[val]:
                    activity[val] = vals[val]
