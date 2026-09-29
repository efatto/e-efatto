from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context


class ProductReplenish(models.TransientModel):
    _inherit = "product.replenish"

    def _prepare_run_values(self):
        values = super()._prepare_run_values()
        # force the vendor selected in the wizard on procurement values
        subcontractor_id = self.env.context.get("subcontractor_id")
        subcontractor_id = getattr(subcontractor_id, "id", subcontractor_id)
        if subcontractor_id:
            supplierinfo = self.product_id.seller_ids.filtered(
                lambda x: x.partner_id.id == subcontractor_id
            )[:1]
            if supplierinfo:
                values["supplierinfo_id"] = supplierinfo
        return values

    def launch_replenishment_with_origin(self):
        # replace original method launch_replenishment to set origin from context
        if not self.route_id:
            raise UserError(_("You need to select a route to replenish your products"))
        uom_reference = self.product_id.uom_id
        self.quantity = self.product_uom_id._compute_quantity(
            self.quantity, uom_reference, rounding_method="HALF-UP"
        )
        self.env["procurement.group"].with_context(
            **clean_context(self.env.context)
        ).run(
            [
                self.env["procurement.group"].Procurement(
                    self.product_id,
                    self.quantity,
                    uom_reference,
                    self.warehouse_id.lot_stock_id,  # Location
                    _("Manual Replenishment"),  # Name
                    self.env.context.get("origin", _("Manual Replenishment")),  # Origin
                    self.warehouse_id.company_id,
                    self._prepare_run_values(),  # Values
                )
            ]
        )
