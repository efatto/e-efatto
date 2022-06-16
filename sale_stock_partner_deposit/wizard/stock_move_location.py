# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockMoveLocationWizard(models.TransientModel):
    _inherit = "wiz.stock.move.location"

    partner_id = fields.Many2one('res.partner')
    create_sale_order = fields.Boolean()

    @api.onchange('create_sale_order')
    def onchange_create_sale_order(self):
        if self.create_sale_order:
            self.destination_location_id = self.env.ref(
                'stock.stock_location_customers')

    @api.onchange('origin_location_id')
    def onchange_origin_location(self):
        super().onchange_origin_location()
        if self.origin_location_id and self.origin_location_id.deposit_location:
            self.partner_id = self.origin_location_id.partner_id

    @api.multi
    def action_move_location(self):
        self.ensure_one()
        if not self.picking_id:
            if not any([x.move_quantity for x in self.stock_move_location_line_ids]):
                raise ValidationError(_('No move quantity found!'))
            picking = self._create_picking()
        else:
            picking = self.picking_id
        # do not recreate moves if created sale order
        if not self.create_sale_order:
            self._create_moves(picking)
        # end difference from original function
        if not self.env.context.get("planned"):
            picking.button_validate()
        else:
            picking.action_confirm()
            picking.action_assign()
        self.picking_id = picking
        return self._get_picking_action(picking.id)

    def _create_picking(self):
        if self.create_sale_order and not self.partner_id:
            raise ValidationError(_('Order can be created only if partner is found!'))
        if self.create_sale_order and self.partner_id:
            sale_order = self.env['sale.order'].create({
                'partner_id': self.partner_id.id,
            })
            self._create_lines(sale_order)
            # TODO check if there is a better method to find route
            rules = self.env['stock.rule'].search([
                ('use_partner_stock_deposit', '=', True),
            ])
            route_id = self.env['stock.location.route'].search([
                ('rule_ids', 'in', rules.ids),
            ], limit=1)
            sale_order.route_id = route_id
            sale_order.action_confirm()
            picking = sale_order.picking_ids[0]
            return picking
        return super()._create_picking()

    @api.multi
    def _create_lines(self, sale_order):
        # Create directly line as shown, to preserve lot if selected (in the original
        # one they are ignored)
        self.ensure_one()
        sale_lines = self.env["sale.order.line"]
        for line in self.stock_move_location_line_ids:
            sale_line = self._create_sale(sale_order, line)
            sale_lines |= sale_line
        return sale_lines

    @staticmethod
    def _get_sale_values(sale_order, line):
        product = line.product_id
        return {
            "name": product.display_name,
            "product_id": product.id,
            "product_uom": line.product_uom_id.id,
            "product_uom_qty": line.move_quantity,
            "order_id": sale_order.id,
            "lot_id": line.lot_id.id,
        }

    @api.multi
    def _create_sale(self, sale_order, line):
        self.ensure_one()
        sale_line = self.env["sale.order.line"].create(
            self._get_sale_values(sale_order, line),
        )
        return sale_line
