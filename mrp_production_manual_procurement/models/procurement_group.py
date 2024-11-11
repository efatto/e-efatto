from odoo import api, models
from odoo.tools import config


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    @api.model
    def run(self, procurements, raise_user_error=True):
        if not config["test_enable"] or self.env.context.get(
            "test_mrp_production_manual_procurement"
        ):
            if self.env.context.get("is_procurement_stopped"):
                # do nothing
                return True

        return super().run(procurements=procurements, raise_user_error=raise_user_error)
