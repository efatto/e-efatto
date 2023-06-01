# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Mrp bom evaluation simple',
    'version': '12.0.1.0.0',
    'category': 'Manufacture',
    'license': 'AGPL-3',
    'author': "Sergio Corato",
    'website': 'https://github.com/sergiocorato/e-efatto',
    'depends': [
        'mrp_bom_operation_estimate',
        'mrp_production_demo',
    ],
    'excludes': [
        'mrp_bom_evaluation',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/mrp_report_bom.xml',
        'views/mrp_bom.xml',
        'report/assets_view.xml',
    ],
    'installable': True,
}
