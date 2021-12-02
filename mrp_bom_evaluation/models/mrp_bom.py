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
                # do not raise error if vendor is not found, leave price unchanged
                continue

            supplier = self.env['stock.rule']._make_po_select_supplier(
                values, suppliers)
            price_unit = self.env['stock.rule']._get_seller_price(
                supplier, line.product_uom_id)
            if price_unit != 0.0:
                line.price_unit = price_unit
                line.price_write_date = supplier.write_date

    @api.multi
    def update_product_managed_replenishment_cost(self):
        self.ensure_one()
        managed_replenishment_cost = sum(
                self.bom_line_ids and self.bom_line_ids.mapped('price_subtotal')
                or [0.0]
            ) + sum(
                self.bom_operation_ids and
                self.bom_operation_ids.mapped('price_subtotal') or [0.0]
            )
        if self.product_id:
            self.product_id.managed_replenishment_cost = managed_replenishment_cost
        elif self.product_tmpl_id:
            self.product_tmpl_id.managed_replenishment_cost = managed_replenishment_cost

    @api.multi
    def add_finishing_product(self):
        self.ensure_one()
        # get finishing products for mrp_bom product computing weight from mrp component
        # wich belongs to product category where a finishing product is set
        finishing_product_id = self.product_tmpl_id.categ_id.finishing_product_id
        if finishing_product_id:
            to_finish_bom_line_ids = self.mapped('bom_line_ids').filtered(
                lambda x: x.product_id.categ_id.finishing_product_id
                and x.product_id.type != 'service'
            )
            total_bom_product_weight_to_finish = sum(
                x.product_id.weight_uom_id._compute_quantity(
                    x.weight_total * x.product_qty, finishing_product_id.uom_id
                ) for x in to_finish_bom_line_ids)
            if total_bom_product_weight_to_finish:
                finishing_product_bom_line_ids = self.bom_line_ids.filtered(
                    lambda y: y.product_id == finishing_product_id
                )
                if finishing_product_bom_line_ids:
                    finishing_product_bom_line_ids[-1].write({
                        'product_qty': total_bom_product_weight_to_finish,
                        'price_unit': finishing_product_id.standard_price,
                    })
                else:
                    self.env['mrp.bom.line'].create({
                        'bom_id': self.id,
                        'product_id': finishing_product_id.id,
                        'product_qty': total_bom_product_weight_to_finish,
                        'product_uom_id': finishing_product_id.uom_id.id,
                        'price_unit': finishing_product_id.standard_price,
                    })
