# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'MRP Production Expected Qty',
    'version': '12.0.1.0.0',
    'development_status': 'Beta',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'summary': 'Save qty expected in extra field.',
    'depends': [
        'mrp_production_demo',
    ],
    'data': [
        'views/mrp_production.xml',
    ],
    'installable': True,
    'post_init_hook': 'copy_expected_qty',
}
