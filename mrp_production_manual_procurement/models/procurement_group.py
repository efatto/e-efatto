from odoo import api, models
from odoo.tools import config


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    @api.model
    def run(
        self, product_id, product_qty, product_uom, location_id, name, origin, values
    ):
        if not config["test_enable"] or self.env.context.get(
            "test_mrp_production_manual_procurement"
        ):
            if self.env.context.get("is_procurement_stopped"):
                # do nothing
                return True

        return super(ProcurementGroup, self).run(
            product_id, product_qty, product_uom, location_id, name, origin, values
        )
