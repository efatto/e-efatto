import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    @api.model
    def run(self, procurements, raise_user_error=True):
        if self.env.context.get("delivery_create_only", False):
            new_procs = []
            Proc = self.env["procurement.group"].Procurement
            for procurement in procurements:
                if procurement.values.get("sale_line_id"):
                    # values.setdefault(
                    #     "company_id",
                    #     self.env["res.company"]._company_default_get("procurement.group"),
                    # )
                    # values.setdefault("priority", "1")
                    # values.setdefault("date_planned", fields.Datetime.now())
                    # rule = self._get_rule(product_id, location_id, values)
                    # if not rule:
                    #     raise UserError(
                    #         _(
                    #             'No procurement rule found in location "%s" for '
                    #             'product "%s".\n Check routes configuration.'
                    #         )
                    #         % (location_id.display_name, product_id.display_name)
                    #     )
                    # action = "pull" if rule.action == "pull_push" else rule.action
                    # if action == "pull":
                    #     if hasattr(rule, "_run_%s" % action):
                    #         getattr(rule, "_run_%s" % action)(
                    #             product_id,
                    #             product_qty,
                    #             product_uom,
                    #             location_id,
                    #             name,
                    #             origin,
                    #             values,
                    #         )
                    #     else:
                    #         _logger.error(
                    #             "The method _run_%s doesn't exist on the procument "
                    #             "rules" % action
                    #         )
                    new_procs.append(
                        Proc(
                            procurement.product_id,
                            procurement.product_qty,
                            procurement.product_uom,
                            procurement.location_id,
                            procurement.name,
                            procurement.origin,
                            procurement.company_id,
                            procurement.values,
                        )
                    )
            return super().run(new_procs, raise_user_error=raise_user_error)
        return super().run(procurements, raise_user_error=raise_user_error)
