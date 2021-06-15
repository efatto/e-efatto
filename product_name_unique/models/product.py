# Copyright (C) 2018 - 2021, Open Source Integrators
# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    name = fields.Char(translate=False)

    _sql_constraints = [
        ('name_uniq', 'unique(name)',
            'Name must be unique across the database!'), ]
