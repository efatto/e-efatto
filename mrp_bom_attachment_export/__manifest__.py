# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Mrp download Zip of components bom attachment',
    'version': '12.0.1.0.0',
    'category': 'Manufacture',
    'license': 'AGPL-3',
    'description': """
    Download zip of attachment of components from production order or bom.
    """,
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'depends': [
        'mrp',
        'product_attachments_button',
    ],
    'data': [
        'wizard/mrp_bom_attachment_export.xml',
    ],
    'installable': True,
}
