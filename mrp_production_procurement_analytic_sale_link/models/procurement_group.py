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
            if values.get('group_id', False) \
                    and not values.get('account_analytic_id', False):
                group_id = values['group_id']
                mrp_id = self.env['mrp.production'].search([
                    ('name', '=', group_id.name),
                ])
                if mrp_id.lead_line_id:
                    values.update({
                        'lead_line_id': mrp_id.lead_line_id.id,
                    })

        return super(ProcurementGroup, self).run(product_id, product_qty,
                                                 product_uom, location_id,
                                                 name, origin, values)
