# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'MRP Production Manual Procurement',
    'version': '12.0.1.0.0',
    'development_status': 'Beta',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'description': 'Add ability to create procurement after production order '
                   'creation.',
    'depends': [
        'mrp_production_procurement_analytic',
        'purchase_line_procurement_group',
        'sale_timesheet',
    ],
    'data': [
        'views/mrp.xml',
    ],
    'installable': True,
}
