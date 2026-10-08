from odoo import api, models


class MrpWorkorderReplan(models.TransientModel):
    _name = "mrp.workorder.replan"
    _description = "Mrp Workorder Replan"

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        return defaults

    def action_done(self):
        self.ensure_one()
        workorders = self.env["mrp.workorder"].browse(self.env.context["active_id"])
        for workorder in workorders:
            workorder.action_replan()
        return {
            "type": "ir.actions.act_window_close",
        }
