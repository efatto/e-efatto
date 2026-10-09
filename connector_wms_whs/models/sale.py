from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    priority = fields.Selection(
        selection_add=[("2", "Very Urgent"), ("3", "Extremely Urgent")],
        ondelete={"2": lambda r: r.write({"priority": "1"}),
                  "3": lambda r: r.write({"priority": "1"})},
        help="Priority of the order:\n"
             "- Normal: within 3 working weeks\n"
             "- Urgent: within 2 working weeks\n"
             "- Very Urgent: within 1 working week\n"
             "- Extremely Urgent: within 24 hours"
    )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    priority = fields.Selection(
        selection_add=[("2", "Very Urgent"), ("3", "Extremely Urgent")],
        ondelete={"2": lambda r: r.write({"priority": "1"}),
                  "3": lambda r: r.write({"priority": "1"})},
        help="Priority of the order:\n"
             "- Normal: within 3 working weeks\n"
             "- Urgent: within 2 working weeks\n"
             "- Very Urgent: within 1 working week\n"
             "- Extremely Urgent: within 24 hours"
    )
