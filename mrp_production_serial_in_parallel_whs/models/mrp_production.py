from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    hide_mark_done = fields.Boolean(
        compute="_compute_hide_mark_done",
    )

    def _compute_hide_mark_done(self):
        for rec in self:
            rec.hide_mark_done = (
                rec.is_parallel_production
                or rec.state not in ["progress", "consumed"]
                or rec.qty_producing == 0
                or (
                    rec.bom_type == "subcontract"
                    or (
                        rec.bom_type != "subcontract"
                        and (rec.is_consumable or not rec.sent_to_whs)
                    )
                )
            )
