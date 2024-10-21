from odoo import models


class QcInspection(models.Model):
    _inherit = "qc.inspection"

    def _prepare_inspection_header(self, object_ref, trigger_line):
        res = super()._prepare_inspection_header(object_ref, trigger_line)
        if trigger_line.note:
            res.update({"internal_notes": trigger_line.note})
        return res
