# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    'name': 'Excel Import/Export/Report Bom',
    'version': '12.0.1.0.1',
    'author': 'Sergio Corato',
    'license': 'AGPL-3',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'category': 'Tools',
    'depends': [
        'excel_import_export',
        'mrp',
    ],
    'data': [
        'import_export_mrp_bom/actions.xml',
        'import_export_mrp_bom/templates.xml',
        'import_mrp_boms/menu_action.xml',
        'import_mrp_boms/templates.xml',
    ],
    'installable': True,
    'development_status': 'Alpha',
}
