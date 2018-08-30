# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    first_name = fields.Char('First Name')
    last_name = fields.Char('Last Name')

