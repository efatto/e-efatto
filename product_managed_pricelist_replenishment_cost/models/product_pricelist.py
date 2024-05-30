from odoo import fields, models


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    # re-translate this field
    base = fields.Selection(
        selection=[
            ("list_price", "Sales Price"),
            ("standard_price", "Cost"),
            ("pricelist", "Other Pricelist"),
            ("managed_replenishment_cost",
             "Landed with adjustment/depreciation/testing"),
        ],
        help="Base price for computation.\n"
        "Sales Price: The base price will be the Sales Price.\n"
        "Cost Price : The base price will be the cost price.\n"
        "Other Pricelist : Computation of the base price based on "
        "another Pricelist.\n"
        "Landed with adjustment/depreciation/testing: The base price will be the "
        "Landed with adjustment/depreciation/testing price.",
    )
