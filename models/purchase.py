from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.onchange('requisition_id')
    def _onchange_requisition_id(self):
        super()._onchange_requisition_id()
        for line in self.requisition_id.line_ids:
            if line.origin and line.origin not in self.origin.split(', '):
                self.origin = self.origin + ', ' + line.origin
