# Copyright 2012-2016 Camptocamp SA
# Copyright 2019 Tecnativa
# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Order point generator rule',
    'summary': 'Mass configuration of stock order points from rules',
    'version': '12.0.1.0.0',
    'category': 'Warehouse',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'license': 'AGPL-3',
    'depends': [
        'product_state',
        'stock_orderpoint_generator',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/orderpoint_template_views.xml',
    ],
    'installable': False,
    'auto_install': False,
}
