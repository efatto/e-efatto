# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_contact_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Contacts',
    )