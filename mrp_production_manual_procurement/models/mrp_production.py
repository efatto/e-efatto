from odoo import api, fields, models
from odoo.tools import config


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    is_procurement_stopped = fields.Boolean(
        compute="_compute_is_procurement_stopped", store=True, copy=False
    )

    @api.depends("move_raw_ids.state")
    def _compute_is_procurement_stopped(self):
        for production in self:
            if production.move_raw_ids:
                is_procurement_stopped = bool(
                    any(move.state == "draft" for move in production.move_raw_ids)
                )
            else:
                is_procurement_stopped = True
            production.is_procurement_stopped = is_procurement_stopped

    def action_confirm(self):
        # Overloaded to pass the context to block procurement run
        self._check_company()
        for prod in self:
            if not config["test_enable"] or self.env.context.get(
                "test_mrp_production_manual_procurement"
            ):
                prod = prod.with_context(
                    is_procurement_stopped=prod.is_procurement_stopped
                )
            super(MrpProduction, prod).action_confirm()
            if not config["test_enable"] or self.env.context.get(
                "test_mrp_production_manual_procurement"
            ):
                # recreate recordset of original moves with original function to restore
                # initial 'draft' state
                move_create_proc = self.env["stock.move"]
                move_waiting = self.env["stock.move"]
                for move in prod.move_raw_ids:
                    if move.move_orig_ids:
                        move_waiting |= move
                    elif move.procure_method == "make_to_order":
                        move_create_proc |= move
                (move_waiting | move_create_proc).write({"state": "draft"})
        return True

    def button_start_procurement(self):
        self._autoconfirm_production()
