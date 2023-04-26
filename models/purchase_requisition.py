from odoo import api, fields, models


class PurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'

    group_id = fields.Many2one('procurement.group')
    origin = fields.Char()

    @api.multi
    def _prepare_purchase_order_line(
            self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        res = super()._prepare_purchase_order_line(
            name=name, product_qty=product_qty, price_unit=price_unit,
            taxes_ids=taxes_ids)
        res.update({  # FIXME ?? TEORICO!!
            'procurement_group_id': self.group_id.id,
            'origin': self.origin,
        })
        return res


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    def _prepare_tender_values(self, product_id, product_qty, product_uom, location_id,
                               name, origin, values):
        return {
            'origin': origin,
            'date_end': values['date_planned'],
            'warehouse_id': values.get('warehouse_id') and values['warehouse_id'].id
            or False,
            'company_id': values['company_id'].id,
            'line_ids': [(0, 0, {
                'product_id': product_id.id,
                'product_uom_id': product_uom.id,
                'product_qty': product_qty,
                'move_dest_id': values.get('move_dest_ids')
                and values['move_dest_ids'][0].id or False,
                'origin': origin,
                'group_id': values.get('group_id') and values['group_id'][0].id
                or False,
                'account_analytic_id': values.get('account_analytic_id') and
                values['account_analytic_id'] or False,
            })],
        }
