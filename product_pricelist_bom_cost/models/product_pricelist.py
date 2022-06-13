# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"
    _order = "applied_on, min_quantity desc, min_value desc, categ_id desc, id desc"

    base = fields.Selection(
        selection_add=[('bom_cost', 'Bom Cost')]
    )
    applied_on = fields.Selection(
        selection_add=[('21_listprice_category', 'Listprice Category')]
    )
    listprice_categ_id = fields.Many2one(
        comodel_name='listprice.category',
        string='Listprice Category',
        ondelete='cascade',
        help="Specify listprice product category on which this rule is applicable"
    )
    min_value = fields.Monetary()
    max_value = fields.Monetary()

    # todo check overlapping values
