# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'MRP Subcontracting Manual Procurement',
    'version': '12.0.1.0.0',
    'development_status': 'Beta',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'summary': 'Add ability to create procurement after production order '
               'creation selecting a subcontractor.',
    'depends': [
        'mrp_production_demo',
        'mrp_subcontracting',
        'purchase_line_procurement_group',
        'sale_timesheet',
    ],
    'data': [
        'wizard/mrp_production_select_subcontractor.xml',
        'views/mrp.xml',
    ],
    'installable': True,
}
