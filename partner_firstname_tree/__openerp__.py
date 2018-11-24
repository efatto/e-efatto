# -*- coding: utf-8 -*-
#
#    Copyright (C) 2016-2017 Sergio Corato
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
#

{
    'name': 'Partner first and last name tree view',
    'version': '8.0.2.0.0',
    'category': 'other',
    'license': 'AGPL-3',
    'description': "Partner first and last name in tree view",
    'author': "Sergio Corato",
    'depends': [
        'base',
        'partner_firstname',
    ],
    'data': [
        'views/partner_view.xml'
    ],
    'installable': True,
}
