# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'CRM lead product identify',
    'version': '12.0.1.0.0',
    'category': 'Sales Management',
    'license': 'AGPL-3',
    'description': """
    Set product type default to stockable product to product created from lead.
    TODO set product name to a code related to crm lead code.
    """,
    'author': "Sergio Corato",
    'website': 'https://efatto.it',
    'depends': [
        'crm_lead_product',
    ],
    'data': [
        'views/crm_lead_line.xml',
    ],
    'installable': True,
}
