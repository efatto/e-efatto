from odoo import fields, models


class QcTriggerLine(models.AbstractModel):
    _inherit = "qc.trigger.line"

    note = fields.Char(string="Internal note")
    lot_internal = fields.Char(string="Internal lot")
    lot_supplier = fields.Char(string="Supplier lot")
