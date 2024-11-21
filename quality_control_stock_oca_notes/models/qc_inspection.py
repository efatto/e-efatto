from odoo import fields, models


class QcInspection(models.Model):
    _inherit = "qc.inspection"

    lot_internal = fields.Text(string="Internal lot")
    lot_supplier = fields.Char(string="Supplier lot")

    def _prepare_inspection_header(self, object_ref, trigger_line):
        res = super()._prepare_inspection_header(object_ref, trigger_line)
        if trigger_line.note:
            res.update({"internal_notes": trigger_line.note})
        if trigger_line.lot_internal:
            res.update({"lot_internal": trigger_line.lot_internal})
        if trigger_line.lot_supplier:
            res.update({"lot_supplier": trigger_line.lot_supplier})
        return res
