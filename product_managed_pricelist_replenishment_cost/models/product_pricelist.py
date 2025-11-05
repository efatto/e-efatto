from odoo import fields, models


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    base = fields.Selection(
        selection_add=[
            ("standard_price", "Landed with depreciation/testing"),
            ("managed_replenishment_cost", "Landed with adjustment/depreciation/testing"),
        ],
        help="Base price for computation.\n"
        "Sales Price: The base price will be the Sales Price.\n"
        "Landed with depreciation/testing: The base price will be the cost price.\n"
        "Other Pricelist : Computation of the base price based on "
        "another Pricelist.\n"
        "Landed with adjustment/depreciation/testing: The base price will be the managed "
        "replenishment cost price.",
    )
