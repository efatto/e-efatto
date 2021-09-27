# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class ProductArchiver(models.TransientModel):
    _name = 'product.archiver'

    from_date = fields.Date(string='Inactive from date', required=True)

    @api.multi
    def archive(self):
        for wizard in self:
            from_date = wizard.from_date
            unavailable_products = self.env['product.product'].search([
                ('qty_available', '=', 0.0),
                ('virtual_available', '=', 0.0),
                ('incoming_qty', '=', 0.0),
                ('outgoing_qty', '=', 0.0),
            ])
            # search moved product after from_date to exclude them
            stock_moved_products = self.env['stock.move.line'].search([
                ('date', '>=', from_date),
                ('product_id', 'in', unavailable_products.ids),
            ])
            moved_product_ids = stock_moved_products.mapped('product_id')
            products_to_archive = [
                x.product_tmpl_id.id for x in unavailable_products
                if x not in moved_product_ids and not x.orderpoint_ids]
            action = dict(
                type='ir.actions.act_window',
                name=_('Products to be archived'),
                res_model='product.template',
                view_mode='tree,form',
                domain=[('id', 'in', products_to_archive)],
                target='current',
            )
            return action
