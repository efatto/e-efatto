# -*- coding: utf-8 -*-
#
#
#    Copyright (C) 2018 Sergio Corato
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
    'name': 'Web view usability',
    'version': '8.0.1.0.0',
    'category': 'other',
    'author': 'Sergio Corato',
    'description': """
Web view usability
==================

Usability issue resolved on web view: 
    * enlarge pop-up view,
    * enlarge open button,
    * enlarge drop-down button.
    """,
    'website': 'http://www.efatto.it',
    'license': 'AGPL-3',
    'depends': [
        'web',
    ],
    'data': [
        'views/web.xml',
    ],
    'installable': True
}
