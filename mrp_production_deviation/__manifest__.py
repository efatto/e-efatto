# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': "Production deviation info",
    'version': '12.0.1.0.1',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'description': 'Add deviation info to production pivot.',
    'depends': [
        'mrp',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/mrp_production_deviation_report.xml',
    ],
    'installable': True,
}
