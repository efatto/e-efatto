# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class ProductArchiver(models.TransientModel):
    _name = 'product.archiver'

    from_date = fields.Date(string='Inactive from date', required=True)
    model = fields.Selection([
        ('product', 'Product Variant'),
        ('template', 'Product Template')],
        string='Model', default='product')

    @api.multi
    def archive(self):
        for wizard in self:
            from_date = wizard.from_date
            unavailable_products = self.env['product.product'].with_context(
                active_test=False
            ).search([
                ('qty_available', '=', 0.0),
                ('virtual_available', '=', 0.0),
                ('incoming_qty', '=', 0.0),
                ('outgoing_qty', '=', 0.0),
                ('create_date', '<=', from_date),
            ])
            # search moved product after from_date to exclude them
            stock_moved_products = self.env['stock.move.line'].with_context(
                active_test=False
            ).search([
                ('date', '>=', from_date),
                ('product_id', 'in', unavailable_products.ids),
            ])
            moved_product_ids = stock_moved_products.mapped('product_id')
            if wizard.model == 'template':
                products_to_archive = [
                    x.product_tmpl_id.id for x in unavailable_products
                    if x not in moved_product_ids and not x.orderpoint_ids]
            else:
                products_to_archive = [
                    x.id for x in unavailable_products
                    if x not in moved_product_ids and not x.orderpoint_ids]
            action = dict(
                type='ir.actions.act_window',
                name=_('Products to be archived'),
                res_model='product.%s' % wizard.model,
                view_mode='tree,form',
                domain=[('id', 'in', products_to_archive)],
                target='current',
            )
            return action
