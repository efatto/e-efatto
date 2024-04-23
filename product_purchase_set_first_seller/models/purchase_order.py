from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _add_supplier_to_product(self):
        self.ensure_one()
        res = super()._add_supplier_to_product()
        # set in every product in order_line the seller of this order as the first one
        for line in self.order_line:
            if len(line.product_id.seller_ids) > 1:
                for sequence, seller in enumerate(line.product_id.seller_ids, 2):
                    if seller.name != self.partner_id:
                        seller.sequence = sequence
                        seller.is_auto_set_first = False
                    else:
                        seller.sequence = 1
                        seller.is_auto_set_first = True
        return res
