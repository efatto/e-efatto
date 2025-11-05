from odoo import fields, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    auto_confirm_production = fields.Boolean(
        default=True,
        help="If un-checked, productions will not be confirmed automatically.",
    )

    def _should_auto_confirm_procurement_mo(self, p):
        res = super()._should_auto_confirm_procurement_mo(p=p)
        if not self.auto_confirm_production:
            res = False
        return res
