from odoo import fields, models


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    base = fields.Selection(
        selection_add=[("managed_replenishment_cost", "Managed Replenishment Cost")],
        ondelete={"managed_replenishment_cost": "set default"},
        help='Base price for computation.\n'
             'Sales Price: The base price will be the Sales Price.\n'
             'Cost Price : The base price will be the cost price.\n'
             'Other Pricelist : Computation of the base price based on '
             'another Pricelist.\n'
             'Managed Replenishment Cost: The base price will be the managed '
             'replenishment cost price.'
    )
