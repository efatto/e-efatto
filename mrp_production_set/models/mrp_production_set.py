from odoo import api, fields, models


class MrpProductionSet(models.Model):
    _name = "mrp.production.set"
    _description = "MRP Production Set"

    name = fields.Char(string="Name")
    production_left_id = fields.Many2one(
        comodel_name="mrp.production",
        # todo domain on the same components of bom? or same product?
        string="Production Left",
    )
    production_right_id = fields.Many2one(
        comodel_name="mrp.production",
        string="Production Right",
    )

    # todo button to start the 2 productions
