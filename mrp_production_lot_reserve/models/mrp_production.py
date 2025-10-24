from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    reserved_lot_ids = fields.Many2many(
        comodel_name="stock.production.lot",
        string="Reserved Lots",
        relation="mrp_production_stock_production_lot_rel",
        column1="mrp_production_id",
        column2="stock_production_lot_id",
    )

    # todo forbid reservation of lots already present in other MO or reserved
