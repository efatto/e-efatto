from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for move in res:
            if move.state == 'confirmed' and move.raw_material_production_id:
                move.write({
                    'state': 'draft',
                    'procure_method': 'make_to_order',  # possibile prenderlo da rule?
                })
        return res
