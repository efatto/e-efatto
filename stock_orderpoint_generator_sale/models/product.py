# Copyright 2017 Camptocamp SA
# Copyright 2019 Tecnativa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _compute_historic_quantities_dict(
            self, location_id=False, from_date=False, to_date=False,
            rule=False):
        """Returns a dict of products with a dict of historic moves as for
           a list of historic stock values resulting from those moves. If
           a location_id is passed, we can restrict it to such location"""
        location_ids = self.env['stock.location'].search(
            [('usage', '=', 'customer')]
        )
        domain_move_out = [
            ('product_id', 'in', self.ids),
            ('location_dest_id', 'in', location_ids.ids),
            # ('transportation_reason', '=', 'sale'), TODO sostituirlo
        ]
        if not to_date:
            to_date = fields.Datetime.now()
        if from_date:
            domain_move_out.append(('date', '>=', from_date))
        domain_move_out.append(('date', '<=', to_date))
        move_obj = self.env['stock.move']
        moves = move_obj.search_read(
            domain_move_out, ['product_id', 'product_qty', 'date'],
            order='date asc')
        # We default the compute the stock value anyway to default the value
        # for products with no moves for the given period
        product_moves_dict = {}
        for move in moves:
            product_moves_dict.setdefault(move['product_id'][0], {})
            product_moves_dict[move['product_id'][0]].update({
                move['date']: {
                    'prod_qty': move['product_qty'],
                }
            })
        for product in self.with_context(prefetch_fields=False):
            # If no there are no moves for a product we default the stock
            # to 0 to update existing rules
            product_moves = product_moves_dict.get(product.id)
            moves_qty = sum([product_moves[y]['prod_qty'] for y in product_moves])\
                if product_moves else 0
            found_rule = False
            if moves_qty:
                if rule.max_move_qty > 0:
                    if rule.min_move_qty < moves_qty < rule.max_move_qty:
                        found_rule = rule
                else:
                    if rule.min_move_qty < moves_qty:
                        found_rule = rule
            if not product_moves:
                product_moves_dict[product.id] = {
                    to_date: {
                        'prod_qty': 0,
                        'stock': 0,
                    },
                    'min_qty': found_rule.min_orderpoint_qty if found_rule else 0,
                    'max_qty': found_rule.max_orderpoint_qty if found_rule else 0,
                    'product_uom': product.uom_id.id,
                }
                continue
            else:
                product_moves_dict[product.id].update({
                    'min_qty': found_rule.min_orderpoint_qty if found_rule else 0,
                    'max_qty': found_rule.max_orderpoint_qty if found_rule else 0,
                    'product_uom': product.uom_id.id,
                })
        return product_moves_dict
