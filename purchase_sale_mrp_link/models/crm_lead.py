# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class CrmLeadLine(models.Model):
    _inherit = "crm.lead.line"

    purchase_ids = fields.One2many(
        comodel_name='purchase.order',
        inverse_name='lead_line_id',
        string="Purchase orders",
    )

    @api.multi
    def name_get(self):
        result = []
        for crm_line in self:
            rec_name = "[%s] %s:%s" % (
                crm_line.lead_id.name,
                crm_line.product_id.default_code,
                crm_line.name)
            result.append((crm_line.id, rec_name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100,
                     name_get_uid=None):
        if not name == '' and operator in ('ilike', 'like', '=', '=like', '=ilike'):
            args = [] if args is None else args.copy()
            args += [
                '|', '|',
                ('name', operator, name),
                ('lead_id.name', operator, name),
                ('product_id.default_code', operator, name)
            ]
            if operator == 'ilike':
                # to exclude extension of args with and & domain
                name = ''
        return super()._name_search(name=name, args=args, operator=operator,
                                    limit=limit, name_get_uid=name_get_uid)
