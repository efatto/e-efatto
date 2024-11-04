# Copyright 2024 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Connector Modula WMS',
    'version': '12.0.1.0.0',
    'category': 'Sales Management',
    'license': 'AGPL-3',
    'summary': """
    Add a field with days to first sale of crm lead, computed on date_sent added on
    sale order.
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
