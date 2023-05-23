# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models
from odoo.tools import config


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    @api.model
    def run(self, product_id, product_qty, product_uom, location_id, name,
            origin, values):
        if not config['test_enable'] or self.env.context.get(
            'test_mrp_production_procurement_analytic'
        ):
            if not values.get('account_analytic_id', False):
                analytic_account_id = False
                if values.get('group_id', False):
                    group_id = values['group_id']
                    mrp_id = self.env['mrp.production'].search([
                        ('name', '=', group_id.name),
                    ])
                    if mrp_id.analytic_account_id:
                        analytic_account_id = mrp_id.analytic_account_id
                    elif group_id.sale_id.analytic_account_id:
                        analytic_account_id = group_id.sale_id.analytic_account_id
                if not analytic_account_id and values.get('sale_line_id', False):
                    order_id = self.env['sale.order.line'].browse(
                        values['sale_line_id']
                    ).order_id
                    if order_id.analytic_account_id:
                        analytic_account_id = order_id.analytic_account_id
                if analytic_account_id:
                    values.update({
                        'account_analytic_id': analytic_account_id.id,
                    })

        res = super(ProcurementGroup, self).run(product_id, product_qty,
                                                product_uom, location_id,
                                                name, origin, values)
        return res
