# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _


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
                    x.product_id.weight * x.product_qty, finishing_product_id.uom_id
                ) for x in to_finish_bom_line_ids) * (
                1 + finishing_product_id.finishing_surcharge_percent / 100.0
            )
            if total_bom_product_weight_to_finish:
                finishing_product_bom_line_ids = self.bom_line_ids.filtered(
                    lambda y: y.product_id == finishing_product_id
                )
                values = {
                    'product_id': finishing_product_id.id,
                    'product_qty': total_bom_product_weight_to_finish,
                    'product_uom_id': finishing_product_id.uom_id.id,
                    'price_unit': finishing_product_id.standard_price,
                }
                if finishing_product_bom_line_ids:
                    finishing_product_bom_line_ids[-1].write(values)
                else:
                    values.update({
                        'bom_id': self.id,
                    })
                    self.env['mrp.bom.line'].create(values)
