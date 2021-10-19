# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    qty_available = fields.Float(string='Quantity On Hand')


class Product(models.Model):
    _inherit = 'product.product'

    qty_available = fields.Float(string='Quantity On Hand')
