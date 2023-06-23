from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    subcontractor_id = fields.Many2one(
        "res.partner",
    )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for move in res:
            if move.state == 'confirmed' and move.raw_material_production_id:
                move.write({
                    'origin': move.raw_material_production_id.origin or
                    move.raw_material_production_id.name,
                    'state': 'draft',
                    'procure_method': 'make_to_order',  # possibile prenderlo da rule?
                })
        return res
