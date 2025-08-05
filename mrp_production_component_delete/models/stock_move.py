from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    is_locked = fields.Boolean(related="raw_material_production_id.is_locked")

    def delete_production_component(self):
        self.ensure_one()
        self._action_cancel()
        self.unlink()
