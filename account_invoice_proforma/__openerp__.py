# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2013 Associazione OpenERP Italia
#    (<http://www.openerp-italia.org>).
#    Copyright (C) 2018 Sergio Corato
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Proforma Invoice',
    'version': '8.0.1.0.0',
    'category': 'Account',
    'description': """
    This module adds a sequence to the proforma invoice.
    """,
    'author': 'OpenERP Italian Community',
    'website': 'http://www.openerp-italia.org/',
    'summary': 'Proforma Invoice',
    'depends': [
        'account',
        'account_auto_fy_sequence',
    ],
    'data': [
        'data/account_data.xml',
        'views/account_invoice.xml'
    ],
    'installable': True,
}
