from odoo import api, fields, models


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    previous_work_order_ids = fields.Many2many(
        comodel_name="mrp.workorder",
        relation="mrp_workorder_previous_rel",
        column1="workorder_id",
        column2="previous_work_order_id",
        compute="_compute_previous_work_order_ids",
        store=True,
        help="Previous workorder of the current one",
    )
    origin = fields.Char(related="production_id.origin")

    @api.depends("production_id.workorder_ids.next_work_order_id")
    def _compute_previous_work_order_ids(self):
        for workorder in self:
            workorder.previous_work_order_ids = (
                workorder.production_id.workorder_ids.filtered(
                    lambda w: w.next_work_order_id == workorder
                )
            )
