from odoo import fields, models


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    note = fields.Text(
        string='Description', related='operation_id.note', readonly=True)
