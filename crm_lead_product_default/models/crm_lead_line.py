# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class CrmLeadLine(models.Model):
    _inherit = "crm.lead.line"
    _order = "sequence,id"

    @api.model
    def _get_mto_route(self):
        mrp_route = self.env.ref(
            'mrp.route_warehouse0_manufacture', raise_if_not_found=False)
        mto_route = self.env.ref('stock.route_warehouse0_mto', raise_if_not_found=False)

        if mrp_route and mto_route:
            return (mrp_route | mto_route).ids
        return []

    sequence = fields.Integer("Sequence", default=1)
    product_default_code = fields.Char()
    product_categ_id = fields.Many2one(comodel_name='product.category')
    product_route_ids = fields.Many2many(
        'stock.location.route', default=lambda self: self._get_mto_route())

    @api.onchange('sequence')
    def onchange_product_default_code(self):
        self.product_default_code = '%s-%s' % (
            self.lead_id.code, self.sequence)
        self.product_categ_id = self.lead_id.product_categ_id.id
