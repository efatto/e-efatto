# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Connector WHS WMS',
    'version': '12.0.1.0.0',
    'category': 'Warehouse Management',
    'license': 'AGPL-3',
    'summary': """
    Add custom method to connect to WhSystem WMS.
    """,
    'author': "Sergio Corato",
    'website': 'https://github.com/sergiocorato/e-efatto',
    'depends': [
        'connector_whs',
        'sale_order_priority',
    ],
    'data': [
    ],
    'installable': True,
}
