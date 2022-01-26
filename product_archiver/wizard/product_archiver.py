# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class ProductArchiver(models.TransientModel):
    _name = 'product.archiver'
    _description = 'Wizard to archive product'

    from_date = fields.Date(string='Inactive from date', required=True)

    @api.multi
    def archive(self):
        for wizard in self:
            # unarchive product.template wich product.product is active
            to_unarchive_product_tmpls = self.env['product.product'].search([
                ]).mapped('product_tmpl_id').filtered(lambda x: not x.active)
            to_unarchive_product_tmpls.write({
                'active': True,
            })
            # archive product.template wich product.product is deactivated
            to_archive_product_tmpls = self.env['product.product'].with_context(
                active_test=False
            ).search([
                ('active', '=', False)
            ]).mapped('product_tmpl_id').filtered(lambda x: x.active)
            to_archive_product_tmpls.write({
                'active': False,
            })
            from_date = wizard.from_date
            unavailable_products = self.env['product.product'].with_context(
                active_test=False
            ).search([
                ('type', '!=', 'service'),
                ('qty_available', '=', 0.0),
                ('virtual_available', '=', 0.0),
                ('incoming_qty', '=', 0.0),
                ('outgoing_qty', '=', 0.0),
                ('create_date', '<=', from_date),
            ])
            # search moved product after from_date to exclude them
            # from stock.move.line
            stock_move_line_products = self.env['stock.move.line'].with_context(
                active_test=False
            ).search([
                ('date', '>=', from_date),
                ('product_id', 'in', unavailable_products.ids),
            ])
            move_line_product_ids = stock_move_line_products.mapped('product_id')
            # from stock.move
            stock_move_products = self.env['stock.move'].with_context(
                active_test=False
            ).search([
                ('date', '>=', from_date),
                ('product_id', 'in', unavailable_products.ids),
            ])
            move_product_ids = stock_move_products.mapped('product_id')
            # from sale.order.line
            sale_order_line_products = self.env['sale.order.line'].with_context(
                active_test=False
            ).search([
                ('order_id.date_order', '>=', from_date),
                ('product_id', 'in', unavailable_products.ids),
            ])
            sale_order_line_product_ids = sale_order_line_products.mapped('product_id')
            # from purchase.order.line
            purchase_order_line_products = self.env['purchase.order.line'].with_context(
                active_test=False
            ).search([
                ('date_order', '>=', from_date),
                ('product_id', 'in', unavailable_products.ids),
            ])
            purchase_order_line_product_ids = purchase_order_line_products.mapped(
                'product_id')
            # from mrp.bom
            mrp_bom_line_products = self.env['mrp.bom.line'].with_context(
                active_test=False
            ).search([
                ('bom_id.active', '=', True),
                ('product_id', 'in', unavailable_products.ids),
            ])
            mrp_bom_line_product_ids = mrp_bom_line_products.mapped('product_id')
            # other? sale line? purchase line? mrp line?
            products_to_archive = [
                x.product_tmpl_id.id for x in unavailable_products
                if x not in move_line_product_ids
                and x not in move_product_ids
                and x not in sale_order_line_product_ids
                and x not in purchase_order_line_product_ids
                and x not in mrp_bom_line_product_ids
                and not x.orderpoint_ids]
            action = dict(
                type='ir.actions.act_window',
                name=_('Products to be archived'),
                res_model='product.template',
                view_mode='tree,form',
                domain=[('id', 'in', products_to_archive)],
                target='current',
            )
            return action
