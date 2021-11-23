# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    total_attachment_ids = fields.Many2many(
        'ir.attachment',
        compute='_compute_total_attachment_count')
    total_attachment_count = fields.Integer(
        '# All Attachments',
        compute='_compute_total_attachment_count')

    @api.multi
    def _compute_total_attachment_count(self):
        for template in self:
            total_attachment_ids = (
                self.env['ir.attachment'].search(
                    ['|', '&',
                     ('res_model', '=', 'product.template'),
                     ('res_id', '=', template.id),
                     '&',
                     ('res_model', '=', 'product.product'),
                     ('res_id', '=', template.product_variant_ids.ids),
                     ])
            )
            template.total_attachment_ids = total_attachment_ids
            template.total_attachment_count = len(total_attachment_ids)

    def action_open_attachments(self):
        domain = [('id', 'in', self.total_attachment_ids.ids)]
        return {
            'type': 'ir.actions.act_window',
            'name': _('All attachments'),
            'domain': domain,
            'views': [(False, 'tree'), (False, 'kanban'), (False, 'form')],
            'res_model': 'ir.attachment',
        }


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_open_attachments(self):
        domain = [('id', 'in', self.product_tmpl_id.total_attachment_ids.ids)]
        return {
            'type': 'ir.actions.act_window',
            'name': _('All attachments'),
            'domain': domain,
            'views': [(False, 'tree'), (False, 'kanban'), (False, 'form')],
            'res_model': 'ir.attachment',
        }
