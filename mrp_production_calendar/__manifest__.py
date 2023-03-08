# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'MRP Production Calendar',
    'version': '12.0.1.0.0',
    'development_status': 'Beta',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'description': 'Add computed field to show duration of production and workorder '
                   'on views.',
    'depends': [
        'mrp_production_demo',
        'mrp_workorder_hierarchy',
        'web_timeline',
    ],
    'data': [
        'views/mrp.xml',
    ],
    'installable': True,
}
