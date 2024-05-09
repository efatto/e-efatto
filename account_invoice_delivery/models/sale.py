from odoo import _, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _create_invoices(self, grouped=False, final=False, date=None):
        if any([x.carrier_id != self[-1].carrier_id for x in self]):
            raise UserError(
                _("Only sale orders with the same carrier can be invoiced together!")
            )
        return super()._create_invoices(grouped=grouped, final=final, date=date)

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        res.update(delivery_carrier_id=self.carrier_id)
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        res.update(is_delivery=self.is_delivery)
        return res
