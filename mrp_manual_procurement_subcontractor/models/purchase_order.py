from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    subcontract_production_picking_ids = fields.Many2many(
        string="Subcontract pickings",
        related="subcontract_production_ids.picking_ids",
    )
    subcontract_production_picking_count = fields.Integer(
        string="Subcontract pickings count",
        compute="_compute_subcontract_production_picking_count",
    )

    def _compute_subcontract_production_picking_count(self):
        for order in self:
            order.subcontract_production_picking_count = len(
                order.subcontract_production_picking_ids
            )

    def action_view_subcontract_picking(self):
        pickings = self.mapped("subcontract_production_picking_ids")
        action = self.env.ref("stock.action_picking_tree_all").read()[0]
        if len(pickings) > 1:
            action["domain"] = [("id", "in", pickings.ids)]
        elif len(pickings) == 1:
            action["views"] = [(self.env.ref("stock.action_picking_form").id, "form")]
            action["res_id"] = pickings[0].id
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action
