# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io
import zipfile
from datetime import datetime
from odoo import models, api, fields, _
from odoo.exceptions import UserError
from odoo.osv import expression


class WizardMrpBomAttachmentExport(models.TransientModel):
    _name = "wizard.mrp.bom.attachment.export"
    _description = 'Wizard MRP BOM attachment export ZIP'

    def _get_product_ids(self):
        product_ids = self.env['product.product']
        if self.env.context['active_model'] == 'mrp.production':
            product_ids = self.env['mrp.production'].browse(
                self.env.context['active_ids']).mapped('move_raw_ids.product_id')
        if self.env.context['active_model'] == 'mrp.bom':
            product_ids = self.env['mrp.bom'].browse(self.env.context['active_ids']).\
                mapped('bom_line_ids.product_id')
        return product_ids

    @api.model
    def _default_name(self):
        obj_ids = self.env[self.env.context['active_model']].browse(
            self.env.context['active_ids'])
        return "%s_%s_%s" % (
            _("BOM"),
            '-'.join(
                hasattr(x, 'product_id') and x.product_id.default_code
                or x.product_tmpl_id.default_code for x in obj_ids),
            datetime.now().strftime('%Y%m%d%H%M'))

    data = fields.Binary("File", readonly=True)
    name = fields.Char('Filename', default=_default_name, required=True)
    and_attachment_ctg_ids = fields.Many2many(
        comodel_name='ir.attachment.category',
        relation="export_ir_attachment_category_and",
        string='Attachment categories with AND logic',
    )
    or_attachment_ctg_ids = fields.Many2many(
        comodel_name='ir.attachment.category',
        relation="export_ir_attachment_category_or",
        string='Attachment categories with OR logic',
    )

    @api.multi
    def export_zip(self):
        self.ensure_one()
        product_ids = self._get_product_ids()
        attachments = product_ids.mapped('product_tmpl_id.all_attachment_ids')
        domain = []
        if self.and_attachment_ctg_ids:
            for and_attachment_ctg_id in self.and_attachment_ctg_ids:
                domain = expression.AND(
                    [domain, [("category_ids", "=", and_attachment_ctg_id.id)]])
        if self.or_attachment_ctg_ids:
            for or_attachment_ctg_id in self.or_attachment_ctg_ids:
                domain = expression.OR(
                    [domain, [("category_ids", "=", or_attachment_ctg_id.id)]])
        domain = expression.AND(
            [domain, [("id", "in", attachments.ids)]]
        )
        attachments = self.env["ir.attachment"].search(domain)
        if not attachments:
            raise UserError(
                _("No attachment found!")
            )
        for att in attachments:
            if not att.datas or not att.datas_fname:
                raise UserError(
                    _("Attachment %s does not have file")
                    % att.display_name)

        fp = io.BytesIO()
        with zipfile.ZipFile(fp, mode="w") as zf:
            for att in attachments:
                zf.writestr(att.datas_fname, base64.b64decode(att.datas))
        fp.seek(0)
        data = fp.read()
        attach_vals = {
            'name': self.name + '.zip',
            'datas_fname': self.name + '.zip',
            'datas': base64.encodebytes(data),
        }
        zip_att = self.env['ir.attachment'].create(attach_vals)
        return {
            'view_type': 'form',
            'name': _("Export component attachments"),
            'res_id': zip_att.id,
            'view_mode': 'form',
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
        }
