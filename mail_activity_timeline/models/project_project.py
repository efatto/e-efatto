from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    activity_color = fields.Char()

    def write(self, values):
        res = super().write(values)
        if not self.env.context.get("bypass_resource_planner"):
            for project in self:
                activity_ids = project.mapped("task_ids.activity_ids").filtered(
                    lambda x: x.is_resource_planner
                )
                if activity_ids:
                    if any(
                        x in values
                        for x in [
                            "activity_color",
                        ]
                    ):
                        activity_ids._compute_planner()
        return res
