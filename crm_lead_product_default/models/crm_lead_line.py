# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class CrmLeadLine(models.Model):
    _inherit = "crm.lead.line"

    #todo impostare un codice progressivo sulla base del codice lead

