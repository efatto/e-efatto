# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'MRP Manual Procurement Subcontractor',
    'version': '12.0.1.0.1',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'summary': 'Add ability to create procurement after production order '
               'creation selecting a subcontractor.',
    'depends': [
        'mrp_production_demo',
        'mrp_subcontracting_purchase_link',
        'purchase_line_procurement_group',
        'sale',  # for test purposes
    ],
    'data': [
        'wizard/mrp_production_procure_subcontractor.xml',
        'views/mrp.xml',
    ],
    'installable': True,
}
