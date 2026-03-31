import base64
import io
import zipfile
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression


class WizardMrpBomAttachmentExport(models.TransientModel):
    _name = "wizard.mrp.bom.attachment.export"
    _description = "Wizard MRP BOM attachment export ZIP"

    def _get_product_ids(self):
        product_ids = []

        def get_all_bom_children(bom_line):
            product_ids.append(bom_line.product_id.id)
            for child in bom_line.child_line_ids:
                product_ids.append(child.product_id.id)
                if child.child_line_ids:
                    product_ids.extend(get_all_bom_children(child))
            return product_ids

        if self.env.context["active_model"] == "mrp.production":
            production_ids = self.env["mrp.production"].browse(
                self.env.context["active_ids"]
            )
            for production_id in production_ids:
                for line in production_id.bom_id.bom_line_ids:
                    product_ids.extend(get_all_bom_children(line))
        if self.env.context["active_model"] == "mrp.bom":
            bom_ids = self.env["mrp.bom"].browse(self.env.context["active_ids"])
            for bom_id in bom_ids:
                for line in bom_id.bom_line_ids:
                    product_ids.extend(get_all_bom_children(line))
        product_ids = list(set(product_ids))
        return product_ids

    @api.model
    def _default_name(self):
        obj_ids = self.env[self.env.context["active_model"]].browse(
            self.env.context["active_ids"]
        )
        return "%s_%s_%s" % (
            _("BOM"),
            "-".join(
                hasattr(x, "product_id")
                and x.product_id.default_code
                or x.product_tmpl_id.default_code
                or ""
                for x in obj_ids
            ),
            datetime.now().strftime("%Y%m%d%H%M"),
        )

    data = fields.Binary("File", readonly=True)
    name = fields.Char("Filename", default=_default_name, required=True)
    and_attachment_ctg_ids = fields.Many2many(
        comodel_name="ir.attachment.category",
        relation="export_ir_attachment_category_and",
        string="Attachment categories with AND logic",
    )
    or_attachment_ctg_ids = fields.Many2many(
        comodel_name="ir.attachment.category",
        relation="export_ir_attachment_category_or",
        string="Attachment categories with OR logic",
    )

    def export_zip(self):
        self.ensure_one()
        product_ids = self._get_product_ids()
        if not product_ids:
            raise UserError(_("No product found!"))
        attachments = (
            self.env["product.product"]
            .browse(product_ids)
            .mapped("product_tmpl_id.all_attachment_ids")
        )
        domain = []
        if self.or_attachment_ctg_ids:
            domain = expression.OR(
                [domain, [("category_ids", "in", self.or_attachment_ctg_ids.ids)]]
            )
        domain = expression.AND([domain, [("id", "in", attachments.ids)]])
        if self.and_attachment_ctg_ids:
            domain = expression.AND(
                [domain, [("category_ids", "in", self.and_attachment_ctg_ids.ids)]]
            )
        attachments = self.env["ir.attachment"].search(domain)
        if not attachments:
            raise UserError(_("No attachment found!"))
        for att in attachments:
            if not att.datas or not att.name:
                raise UserError(
                    _("Attachment %s does not have file") % att.display_name
                )

        fp = io.BytesIO()
        with zipfile.ZipFile(fp, mode="w") as zf:
            for att in attachments:
                zf.writestr(att.name, base64.b64decode(att.datas))
        fp.seek(0)
        data = fp.read()
        attach_vals = {
            "name": self.name + ".zip",
            "store_fname": self.name + ".zip",
            "datas": base64.encodebytes(data),
        }
        zip_att = self.env["ir.attachment"].create(attach_vals)
        return {
            "view_type": "form",
            "name": _("Export component attachments"),
            "res_id": zip_att.id,
            "view_mode": "form",
            "res_model": "ir.attachment",
            "type": "ir.actions.act_window",
        }
