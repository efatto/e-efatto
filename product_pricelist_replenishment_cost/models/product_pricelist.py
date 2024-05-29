from odoo import fields, models


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    base = fields.Selection(
        selection_add=[("managed_replenishment_cost", "Managed Replenishment Cost")],
        ondelete={"managed_replenishment_cost": "set default"},
    )
