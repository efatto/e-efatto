from odoo import api, fields, models, _


class MailActivity(models.Model):
    _inherit = 'mail.activity'

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

    _sql_constraints = [
        (
            "activity_planner_unique",
            "UNIQUE (res_model, res_id, is_resource_planner)",
            "Another planner activity exists for the linked object by model and id.",
        ),
    ]

    def write(self, values):
        res = super().write(values)

        for activity in self:
            if activity.is_resource_planner:
                if any(x in values for x in [
                    'date_start',
                    'date_end',
                    'user_id',
                    'parent_id'
                ]):
                    res_object = self.env[activity.res_model].browse(
                        activity.res_id)
                    vals = {}
                    if activity.res_model == 'mrp.workorder':
                        if 'date_start' in values:
                            vals.update({
                                'date_planned_start': values['date_start']
                            })
                        if 'date_end' in values:
                            vals.update({
                                'date_planned_finished': values['date_end']
                            })
                        if 'user_id' in values:
                            vals.update({'user_id': values['user_id']})
                        if 'parent_id' in values:
                            vals.update({'parent_id': values['parent_id']})
                    elif activity.res_model == 'project.task':
                        if 'date_start' in values:
                            vals.update({
                                'date_start': values['date_start']
                            })
                        if 'date_end' in values:
                            vals.update({
                                'date_end': values['date_end']
                            })
                        if 'user_id' in values:
                            vals.update({'user_id': values['user_id']})
                        if 'parent_id' in values:
                            vals.update({'parent_id': values['parent_id']})
                    res_object.with_context(
                        bypass_resource_planner=True
                    ).write(vals)
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
        }
        res = self.create(vals)
        res._compute_planner()
        return res

    @api.multi
    def _compute_planner(self):
        for activity in self:
            if activity.res_model and activity.res_id:
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
            else:
                activity.date_start = False
                activity.date_end = False

    @api.multi
    def open_res_object(self):
        self.ensure_one()
        res_object = self.env[self.res_model].browse(self.res_id)
        domain = [('id', 'in', res_object.ids)]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Linked %s' % self.res_model),
            'domain': domain,
            'views': [(False, 'tree'), (False, 'kanban'), (False, 'form')],
            'res_model': self.res_model,
        }
