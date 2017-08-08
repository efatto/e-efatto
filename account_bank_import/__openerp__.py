# -*- coding: utf-8 -*-
#
#
#    Copyright (C) 2016-2017 Sergio Corato
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
{
    "name": "Bank Import",
    "version": "8.0.0.0.0",
    "description": """
    This module allows to load bank list from a file.
    The file format must have these columns:

    keys = ['abi', 'cab', 'name', 'street', 'city', 'zip', 'state']
    """,
    'category': 'other',
    'author': 'Sergio Corato',
    'website': 'http://www.efatto.it',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'l10n_it_abicab',
    ],
    'data': [
        'wizard/import_bank_file_view.xml',
     ],
    'installable': True,
    'post_init_hook': 'post_init_hook'
}
