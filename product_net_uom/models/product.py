# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    net = fields.Float(
        digits=dp.get_precision('Net'),
        help='Development of solid'
    )
    net_uom_id = fields.Many2one(
        "uom.uom",
        string="Net Unit of Measure",
        domain="[('measure_type', '=', 'net')]",
        default=lambda x: x._get_net_uom_id_from_ir_config_parameter(),
    )
    net_uom_name = fields.Char(
        string="Net unit of measure label",
        related="net_uom_id.name",
        readonly=True,
    )

    @api.model
    def _get_net_uom_id_from_ir_config_parameter(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        default_uom = get_param("product_default_net_uom_id")
        if default_uom:
            return self.env["uom.uom"].browse(int(default_uom))
        else:
            # no super available in v12
            return self.env["uom.uom"].search(
                [("measure_type", "=", "net"), ("uom_type", "=", "reference")],
                limit=1,
            )
