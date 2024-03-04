
from odoo import models


class QcInspection(models.Model):
    _inherit = "qc.inspection"

    def _make_inspection(self, object_ref, trigger_line):
        # do not create inspection if already created
        if object_ref._name == "stock.move":
            inspection = self.search([
                ("object_id", "=", object_ref.id),
                ("product_id", "=", trigger_line.product.id),
                ("picking_id", "=", object_ref.picking_id.id)
            ])
            if inspection:
                inspection.set_test(trigger_line)
                return inspection
        inspection = super()._make_inspection(object_ref, trigger_line)
        return inspection
