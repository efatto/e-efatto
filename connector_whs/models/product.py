# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    exclude_from_whs = fields.Boolean(
        string="Exclude from WMS sync"
    )
