# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Mrp production qr code',
    'version': '12.0.1.0.0',
    'category': 'Manufacture',
    'license': 'AGPL-3',
    'description': """
    Add qr code to production in form <res_model>_<res_id>.
    """,
    'author': 'Sergio Corato',
    'website': 'https://efatto.it',
    'depends': [
        'mrp',
    ],
    'data': [
        'report/mrp_report_qr_code.xml',
    ],
    'installable': True,
}
