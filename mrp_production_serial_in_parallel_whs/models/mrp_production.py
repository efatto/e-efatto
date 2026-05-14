from odoo import api, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.depends(
        "state",
        "is_parallel_production",
        "qty_producing",
        "bom_type",
        "sent_to_whs",
    )
    def _compute_hide_mark_done(self):
        res = super()._compute_hide_mark_done()
        for rec in self:
            rec.hide_mark_done = (
                rec.is_parallel_production
                or rec.state not in ["progress", "consumed"]
                or rec.qty_producing == 0
                or (
                    rec.bom_type == "subcontract"
                    or (
                        rec.bom_type != "subcontract"
                        and not rec.sent_to_whs
                    )
                )
            )
        return res
