# -*- coding: utf-8 -*-
# Copyright 2018 Sergio Corato
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Add field agents in ddt',
    'version': '8.0.1.0.0',
    'category': 'Invoice Management',
    'license': 'AGPL-3',
    'website': 'https://efatto.it',
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
