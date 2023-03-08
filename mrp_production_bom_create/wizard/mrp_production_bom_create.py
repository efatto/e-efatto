# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MrpProductionBomCreate(models.TransientModel):
    _name = 'mrp.production.bom.create'
    _description = 'Create bom from production order'

    name = fields.Char(
        default=lambda self: self.env['mrp.production'].browse(
            self.env.context['active_id']).product_id.default_code
    )

    @api.multi
    def action_done(self):
        self.ensure_one()
        production = self.env['mrp.production'].browse(
            self.env.context['active_ids'])
        components_values = self.get_components_values(production)
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': production.product_id.product_tmpl_id.id,
            'code': self.name,
            'type': 'normal',
            'routing_id': production.routing_id.id,
            'product_qty': 1,
            'sequence': 1,
            'product_uom_id': production.product_id.uom_id.id,
            'bom_line_ids': [
                (0, 0, x) for x in components_values],
        })
        return {
            'view_type': 'form',
            'name': "MRP Bom",
            'view_mode': 'tree,form',
            'res_model': 'mrp.bom',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', bom.ids)],
        }

    @api.model
    def get_components_values(self, production):
        component_values = []
        for line in production.move_raw_ids.filtered(lambda x: x.quantity_done):
            component_values.append({
                'product_id': line.product_id.id,
                'product_qty': line.quantity_done / (production.product_qty or 1),
                'product_uom_id': line.product_id.uom_id.id,
            })
        return component_values
