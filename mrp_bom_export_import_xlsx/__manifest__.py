# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Mrp Bom Export/Import',
    'version': '12.0.1.0.0',
    'category': 'Manufacture',
    'license': 'AGPL-3',
    'description': """
    Download or upload xlsx of Bom lines.
    """,
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'depends': [
        'mrp_flattened_bom_xlsx',
    ],
    'data': [
        'report/mrp_bom_export.xml',
        'wizard/mrp_bom_import.xml',
    ],
    'installable': True,
}
