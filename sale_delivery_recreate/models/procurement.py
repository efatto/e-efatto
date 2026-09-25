import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    @api.model
    def run(self, procurements, raise_user_error=True):
        if self.env.context.get("delivery_create_only", False):
            new_procs = []
            Proc = self.env["procurement.group"].Procurement
            for procurement in procurements:
                if procurement.values.get("sale_line_id"):
                    new_procs.append(
                        Proc(
                            procurement.product_id,
                            procurement.product_qty,
                            procurement.product_uom,
                            procurement.location_id,
                            procurement.name,
                            procurement.origin,
                            procurement.company_id,
                            procurement.values,
                        )
                    )
            return super().run(new_procs, raise_user_error=raise_user_error)
        return super().run(procurements, raise_user_error=raise_user_error)
