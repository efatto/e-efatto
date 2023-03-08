from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _action_launch_stock_rule(self):
        # only create the procurement group without launching run()
        res = super()._action_launch_stock_rule()
        todo_lines = self.filtered(
            lambda x: x.product_id.type == 'service'
            and x.product_id.service_create_procurement_group
        )
        for line in todo_lines:
            if line.state != 'sale':
                continue
            group_id = line.order_id.procurement_group_id
            if not group_id:
                group_id = self.env['procurement.group'].create({
                    'name': line.order_id.name,
                    'move_type': line.order_id.picking_policy,
                    'sale_id': line.order_id.id,
                    'partner_id': line.order_id.partner_shipping_id.id,
                })
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({
                        'partner_id': line.order_id.partner_shipping_id.id
                    })
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)
        return res
