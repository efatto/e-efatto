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
    'name': 'Add field agents in ddt',
    'version': '8.0.1.0.0',
    'category': 'Invoice Management',
    'license': 'AGPL-3',
    'description': """
    Add tecnical field agents in ddt to use when needed.
    """,
    'author': "Sergio Corato",
    'depends': [
        'sale_order_agents',
        'sale_commission',
        'l10n_it_ddt',
        'stock_picking_tree_sales',
    ],
    'data': [
        'views/ddt.xml'
    ],
    'installable': False,
}
