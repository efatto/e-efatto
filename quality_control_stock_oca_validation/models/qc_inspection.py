from odoo import models


class QcInspection(models.Model):
    _inherit = "qc.inspection"

    def _make_inspection(self, object_ref, trigger_line):
        # do not create inspection if already created
        picking_id = object_ref
        if object_ref._name in ["stock.move", "stock.move.line"]:
            picking_id = object_ref.picking_id
        domain = [
            ("product_id", "=", object_ref.product_id.id),
            ("picking_id", "=", picking_id.id),
        ]
        if object_ref.production_id:
            domain += [("production_id", "=", object_ref.production_id.id)]
        inspection_ids = self.sudo().search(domain)
        if inspection_ids:
            for inspection in inspection_ids:
                if (
                    object_ref._name in ["stock.move", "stock.move.line"]
                    and inspection.object_id == object_ref
                ):
                    inspection.set_test(trigger_line)
            return inspection_ids
        inspection = super()._make_inspection(object_ref, trigger_line)
        return inspection
