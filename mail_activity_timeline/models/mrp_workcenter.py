from odoo import fields, models


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Assigned user',
        index=True,
    )
