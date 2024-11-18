from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MrpProductionProcureSubcontractor(models.TransientModel):
    _name = "mrp.production.procure.subcontractor"
    _description = "Procure from subcontractor"

    subcontractor_ids = fields.Many2many(
        string="Subcontractors", comodel_name="res.partner"
    )
    subcontractor_id = fields.Many2one(
        string="Subcontractor", comodel_name="res.partner"
    )
    route_id = fields.Many2one(comodel_name="stock.location.route")

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get("active_id", False)
        mo = self.env["mrp.production"].browse(active_id)
        if mo.state == "done":
            raise UserError(_("Production in state 'done' cannot be changed!"))
        if mo.product_id.bom_ids.filtered(lambda x: x.type == "subcontract"):
            bom_id = mo.product_id.bom_ids.filtered(lambda x: x.type == "subcontract")[
                0
            ]
            if bom_id.subcontractor_ids:
                defaults["subcontractor_ids"] = bom_id.subcontractor_ids.ids
            else:
                raise UserError(_("Production cannot be set without subcontractors!"))
        else:
            raise UserError(_("Production cannot be set without subcontracted bom!"))
        return defaults

    def action_done(self):
        # cancel current mo and create a new mo for subcontractor with buy route
        self.ensure_one()
        buy_route = self.env.ref("purchase_stock.route_warehouse0_buy")
        mo = self.env["mrp.production"].browse(self.env.context["active_id"])
        mo.action_cancel()
        replenish_wizard = (
            self.env["product.replenish"]
            .with_context(
                subcontractor_id=self.subcontractor_id,
                origin=mo.name,
                proceed_to_production=True,
            )
            .create(
                {
                    "product_id": mo.product_id.id,
                    "product_tmpl_id": mo.product_id.product_tmpl_id.id,
                    "product_uom_id": mo.product_uom_id.id,
                    "quantity": mo.product_qty,
                    "warehouse_id": mo.picking_type_id.warehouse_id.id,
                    "route_ids": [(6, 0, buy_route.ids)],
                }
            )
        )
        replenish_wizard.launch_replenishment_with_origin()
        po_ids = self.env["purchase.order"].search(
            [
                ("origin", "=ilike", mo.name),
                ("order_line.product_id", "=", mo.product_id.id),
            ]
        )
        mo_ids = self.env["mrp.production"].search(
            [
                ("origin", "=", mo.name),
            ]
        )
        if po_ids and not mo_ids:
            mo_ids = po_ids.mapped("subcontract_production_ids")
        if not mo_ids:
            purchase_orders = self.env["purchase.order"].search(
                [
                    ("order_line.product_id", "=", mo.product_id.id),
                    ("state", "=", "purchase"),
                ]
            )
            if purchase_orders:
                purchase_orders = purchase_orders.filtered(
                    lambda x: mo.name in x.origin
                )
                if len(purchase_orders) == 1:
                    purchase_order = purchase_orders[0]
                    purchase_order.button_confirm()
                    mo_ids = purchase_order.subcontract_production_ids
        if len(mo_ids) == 1:
            return {
                "type": "ir.actions.act_window",
                "name": "Mrp production",
                "view_mode": "form",
                "view_type": "form",
                "res_id": mo_ids[0].id,
                "views": [(False, "form")],
                "res_model": "mrp.production",
            }
        else:
            return {
                "type": "ir.actions.act_window",
                "name": "Mrp production",
                "domain": [("id", "in", mo_ids.ids)],
                "view_mode": "form",
                "view_type": "tree",
                "views": [(False, "tree")],
                "res_model": "mrp.production",
            }
