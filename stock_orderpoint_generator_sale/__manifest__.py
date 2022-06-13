# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Order point generator sale',
    'summary': 'Mass configuration of stock order points',
    'version': '12.0.1.0.0',
    'author': "Sergio Corato",
    'category': 'Warehouse',
    'license': 'AGPL-3',
    'website': "https://efatto.it",
    'depends': [
        'product_sellers_info',
        'stock_orderpoint_generator',
    ],
    'data': [
        "views/orderpoint_template_views.xml",
    ],
    'installable': True,
    'auto_install': False,
}
