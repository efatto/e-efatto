# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io
import zipfile
from datetime import datetime
from odoo import models, api, fields, _
from odoo.exceptions import UserError


class WizardMrpBomAttachmentExport(models.TransientModel):
    _name = "wizard.mrp.bom.attachment.export"
    _description = 'Wizard MRP BOM attachment export ZIP'

    @api.model
    def _default_product_ids(self):
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
        return "%s_%s_%s" % (
            _("BOM"),
            '-'.join(x.default_code for x in self.product_ids),
            datetime.now().strftime('%Y%m%d%H%M'))

    product_ids = fields.Many2many(
        comodel_name='product.product',
        default=_default_product_ids,
        required=True,
    )
    data = fields.Binary("File", readonly=True)
    name = fields.Char('Filename', default=_default_name, required=True)
    attachment_ctg_ids = fields.Many2many(
        'ir.attachment.category',
        string='Attachment categories',
    )

    @api.multi
    def export_zip(self):
        self.ensure_one()
        attachments = self.product_ids.mapped('product_tmpl_id.all_attachment_ids')
        if self.attachment_ctg_ids:
            attachments = attachments.filtered(
                lambda x: any(y in self.attachment_ctg_ids for y in x.category_ids))
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
