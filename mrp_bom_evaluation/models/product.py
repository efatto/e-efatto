# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    exclude_from_mo = fields.Boolean(
        help="Used to exclude products that will be used outside manufacturing "
             "process, e.g. during the assembly on site, but included in bom for "
             "evaluation purpose.")
