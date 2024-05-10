from odoo import fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    def _get_default_weight_uom_id(self):
        return self.env[
            'product.template']._get_weight_uom_id_from_ir_config_parameter()

    dimensions = fields.Text(string="Dimensions")
    weight_custom = fields.Float(string="Weight custom")
    weight_custom_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string='Weight unit of measure',
        default=_get_default_weight_uom_id)
    appearance = fields.Text(string="Appearance")
