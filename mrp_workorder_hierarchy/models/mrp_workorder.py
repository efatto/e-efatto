from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'
    _parent_store = True
    _parent_name = "parent_id"

    complete_name = fields.Char(compute="_compute_complete_name", store=True, )
    parent_id = fields.Many2one(
        comodel_name="mrp.workorder",
        string="Parent Workorder",
        ondelete="cascade",
        index=True,
        domain="[('production_id', '=', production_id)]"
    )
    child_workorder_ids = fields.One2many(
        comodel_name="mrp.workorder",
        inverse_name="parent_id",
        string="Child Workorders",
    )
    parent_path = fields.Char(string="Parent Path", index=True)

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for workorder in self:
            if workorder.parent_id:
                workorder.complete_name = "{} / {}".format(
                    workorder.parent_id.complete_name, workorder.name,
                )
            else:
                workorder.complete_name = workorder.name

    @api.multi
    def button_start(self):
        self.ensure_one()
        if self.parent_id and self.parent_id.state not in ['progress', 'done']:
            raise UserError(_('Parent workorder has not been processed!'))
        return super().button_start()
