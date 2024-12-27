# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Connector WMS and Repair',
    'version': '12.0.1.0.0',
    'category': 'Warehouse Management',
    'license': 'AGPL-3',
    'summary': """
    Glue module when connector to WMS and repair are intalled.
    """,
    'author': "Sergio Corato",
    'website': 'https://github.com/sergiocorato/e-efatto',
    'depends': [
        'connector_wms_whs',
        'repair',
    ],
    'data': [
    ],
    'installable': True,
    'auto_install': True,
}
