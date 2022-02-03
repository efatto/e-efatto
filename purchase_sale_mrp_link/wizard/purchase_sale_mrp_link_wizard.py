# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PurchaseSaleMrpLinkWizard(models.TransientModel):
    _name = 'purchase.sale.mrp.link.wizard'
    _description = 'Link a vendor RdP to Sale Offer'

    sale_order_id = fields.Many2one(
        'sale.order', string='Sale Offer', required=True)
    purchase_order_id = fields.Many2one(
        'purchase.order', string='Purchase Order', required=True)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'purchase_order_id' in fields and not res.get('purchase_order_id')\
            and self._context.get('active_model') == 'purchase.order'\
                and self._context.get('active_id'):
            res['purchase_order_id'] = self._context['active_id']
        return res

    @api.multi
    def action_done(self):
        for wizard in self:
            sale_order = wizard.sale_order_id
            purchase_order = wizard.purchase_order_id
            for sale_line in sale_order.order_line:
                if sale_line.product_id:
                    if not sale_line.product_id.bom_ids:
                        #  se è un prodotto senza distinta base:
                        #  se il prodotto è dentro l'so direttamente, linkare la riga
                        #  con la riga dell'SO
                        purchase_line = purchase_order.order_line.filtered(
                            lambda x: x.product_id == sale_line.product_id
                        )
                        if purchase_line:
                            sale_line.purchase_line_id = purchase_line
                    else:
                        # se è un prodotto con distinta base:
                        # linkare le singole righe dei componenti della distinta base
                        # senza tener conto delle possibili distinte base figlie
                        # todo in caso di più distinte quali prendere? adesso le prendo
                        #  tutte
                        for bom_line in sale_line.product_id.mapped(
                                'bom_ids.bom_line_ids'):
                            purchase_line = purchase_order.order_line.filtered(
                                lambda x: x.product_id == bom_line.product_id
                            )
                            if purchase_line:
                                bom_line.purchase_order_line_id = purchase_line
                                sale_line.purchase_line_id = purchase_line
        return {}
