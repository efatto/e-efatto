# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models, _
from odoo.tools.date_utils import relativedelta
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_assign(self):
        # do the check after reservation, as a product can be reserved from many moves
        res = super()._action_assign()
        # todo add option to bypass check
        if self:
            product_ids = self.mapped('product_id')
            available_info = {}
            # dict of dict with:
            # {product_id: {move_date: virtual_available_at_date_expected}}
            today = fields.Date.today()
            for product_id in product_ids:
                available_info.update({product_id.id: {}})
                domain_quant_loc, domain_move_in_loc, domain_move_out_loc = \
                    product_id._get_domain_locations()
                incoming_stock_moves = self.env['stock.move'].search([
                    ('product_id', '=', product_id.id),
                    ('product_uom_qty', '>', 0),
                    ('state', 'not in', ['done', 'cancel']),
                    ('date', '>=', today),
                ] + domain_move_in_loc)
                reserved_stock_moves = self.env['stock.move'].search([
                    ('product_id', '=', product_id.id),
                    ('product_uom_qty', '>', 0),
                    ('state', 'not in', ['done', 'cancel']),
                    ('date', '>=', today),
                ] + domain_move_out_loc)
                for move_date in (
                    set(
                        [x.date() for x in reserved_stock_moves.mapped('date_expected')]
                        + [y.date() for y in incoming_stock_moves.mapped('date_expected')]
                    )
                ):
                    available_info[product_id.id].update({
                        move_date: product_id.with_context(
                            to_date=move_date
                        ).virtual_available_at_date_expected
                    })
            for move in self:
                if move.date_expected:
                    # limit check to date >= expected date
                    product_dict = available_info[move.product_id.id]
                    product_available_info = {
                        x: product_dict[x]
                        for x in product_dict
                        if x >= move.date_expected.date()}
                    # extend available_info with move.date_expected
                    product_available_info.update({
                        move.date_expected.date():
                            move.product_id.with_context(
                                to_date=move.date_expected
                        ).virtual_available_at_date_expected
                    })
                    # remove dates after purchasable date (n.b. a reorder rule must
                    # exits to cover the request)
                    purchasable_date = today + relativedelta(
                        days=move.product_id.purchase_delay)
                    date_not_available_info = {
                        x: product_available_info[x]
                        for x in product_available_info
                        if x < purchasable_date
                        and (
                            product_available_info[x] < 0
                            or
                            product_available_info[x] < move.product_qty
                        )}
                    if date_not_available_info:
                        raise ValidationError(_(
                            "Reservation of product %s not possible for date %s!\n"
                            "Purchasable date: %s\n"
                            "Exception availability info:\n%s" % (
                                move.product_id.name,
                                move.date_expected.strftime('%d/%m/%Y'),
                                purchasable_date.strftime('%d/%m/%Y'),
                                ''.join([
                                    'Date: %s qty: %s\n' % (
                                        x.strftime('%d/%m/%Y'),
                                        date_not_available_info[x])
                                    for x in date_not_available_info
                                ]),
                            )
                        ))
        return res
