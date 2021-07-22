# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MrpRouting(models.Model):
    _inherit = 'mrp.routing'

    routing_revision = fields.Char(string="Revision")
