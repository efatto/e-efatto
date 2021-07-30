# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    total_amount = fields.Float(
        compute='_compute_total_amount',
        store=True)

    @api.multi
    @api.depends('bom_operation_ids.price_subtotal',
                 'bom_line_ids.price_subtotal')
    def _compute_total_amount(self):
        for bom in self:
            bom.total_amount = (
                sum(bom.mapped('bom_operation_ids.price_subtotal'))
                + sum(bom.mapped('bom_line_ids.price_subtotal')))

    @api.multi
    def get_supplier_product_prices(self):
        self.ensure_one()
        for line in self.bom_line_ids:
            product_id = line.product_id
            values = {
                'product_id': product_id,
                'product_qty': line.product_qty,
                'product_uom': line.product_uom_id,
                'company_id': line.bom_id.company_id,
            }
            suppliers = product_id.seller_ids \
                .filtered(lambda r: (not r.company_id or r.company_id == values[
                    'company_id']
                ) and (
                    not r.product_id or r.product_id == product_id) and r.name.active)
            if not suppliers:
                msg = _(
                    'There is no vendor associated to the product %s. '
                    'Please define a vendor for this product.') % (
                        product_id.display_name,)
                raise UserError(msg)

            supplier = self.env['stock.rule']._make_po_select_supplier(
                values, suppliers)
            line.price_unit = self.env['stock.rule']._get_seller_price(
                supplier, line.product_uom_id)

    @api.multi
    def update_product_managed_replenishment_cost(self):
        self.ensure_one()
        self.product_id.managed_replenishment_cost = sum(
            self.bom_line_ids.mapped('price_subtotal')
        ) + sum(
            self.bom_operation_ids.mapped('price_subtotal')
        )
