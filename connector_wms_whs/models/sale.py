from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    priority = fields.Selection(
        selection_add=[("2", "Very Urgent")],
        ondelete={"2": lambda r: r.write({"priority": "1"})},
    )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    priority = fields.Selection(
        selection_add=[("2", "Very Urgent")],
        ondelete={"2": lambda r: r.write({"priority": "1"})},
    )
