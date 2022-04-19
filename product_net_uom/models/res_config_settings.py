# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    product_default_net_uom_id = fields.Many2one(
        "uom.uom",
        "Default Net Unit of Measure",
        domain="[('measure_type', '=', 'net')]",
        config_parameter='product_default_net_uom_id',
        help="Default unit of measure to express product net solid development",
    )
