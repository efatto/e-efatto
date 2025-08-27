from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    transfer_date = fields.Datetime(
        string="Transfer date",
    )

    def _action_done(self):
        res = super()._action_done()
        if self.transfer_date:
            self.write({"date_done": self.transfer_date})
        return res
