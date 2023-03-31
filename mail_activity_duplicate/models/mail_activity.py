from odoo import models, _


class MailActivity(models.Model):
    _inherit = 'mail.activity'

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
