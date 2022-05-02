# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models, fields


class StockRule(models.Model):
    _inherit = 'stock.rule'

    use_partner_stock_deposit = fields.Boolean()

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id,
                               name, origin, values, group_id):
        move_values = super()._get_stock_move_values(
            product_id, product_qty, product_uom, location_id,
            name, origin, values, group_id
        )
        # TODO perchè non viene attivata la rule della route???
        #  qui prendo tutte quelle collegate alle route trovate
        for route in values.get('route_ids'):
            for rule in route.rule_ids:
                if rule.use_partner_stock_deposit and values.get('sale_line_id'):
                    sale_line_id = values['sale_line_id']
                    if isinstance(sale_line_id, int):
                        sale_line_id = self.env['sale.order.line'].browse(sale_line_id)
                    location_src_id = sale_line_id.order_id.partner_id.\
                        property_stock_deposit
                    if location_src_id:
                        move_values['location_id'] = location_src_id.id
        return move_values
