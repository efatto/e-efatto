from odoo import api, fields, models


class MailActivityType(models.Model):
    _inherit = 'mail.activity.type'


    # TODO: Creare in automatico un oggetto 'resource.assignment' da n oggetti
    #  creati/modificati/eliminati, mostrando quindi una vista timeline in cui le
    #  modifiche di data inizio, data fine/durata siano riportate sull'oggetto origine.
    #  Usare un campo res_model_id -> project.task o mrp.workorder o event ecc.
    #  e res_id -> id della risorsa collegata, per gestire la risorsa collegata.
    #  Per comodità creare un mixin da riutilizzare sugli oggetti da tracciare.
    is_resource_planner = fields.Boolean()
    date_start_field = fields.Many2one(
        comodel_name='ir.model.fields'
    )
    date_end_field = fields.Many2one(
        comodel_name='ir.model.fields'
    )
    #todo aggiungere campo di default_group_by -> forse l'utente assegnato sull'oggetto?
    _sql_constraints = [
        (
            "activity_planner_type_unique",
            "UNIQUE (res_model_id, is_resource_planner)",
            "Another planner activity type exists for the linked res model.",
        ),
    ]

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    is_resource_planner = fields.Boolean(
        related='activity_type_id.is_resource_planner',
        store=True,
    )
    date_start = fields.Datetime(
        compute='_compute_dates',
        store=True,
    )
    date_end = fields.Datetime(
        compute='_compute_dates',
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
    # def write(self, values):
    #     res = super().write(values)
    #     self.with_context(bypass_resource_planner=True)
    #     return res

    @api.model
    def create_planner_activity(self, object):
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
            'name': object.name,
            'partner_id': object.partner_id.id,
            'commercial_partner_id': object.partner_id.commercial_partner_id.id,
            'parent_id': object.parent_id.id,
            'user_id': object.user_id.id,
            'is_resource_planner': True,
        }
        res = self.create(vals)
        res._compute_dates()
        return res

    @api.multi
    def update_dates(self):
        self._compute_dates()

    @api.multi
    def _compute_dates(self):
        # todo force recompute as depends is not possible
        for activity in self:
            if activity.res_model and activity.res_id \
                    and activity.activity_type_id.date_start_field \
                    and activity.activity_type_id.date_end_field:
                res_object = self.env[activity.res_model].browse(activity.res_id)
                activity.date_start = getattr(
                    res_object, activity.activity_type_id.date_start_field.name)
                activity.date_end = getattr(
                    res_object, activity.activity_type_id.date_end_field.name)
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
