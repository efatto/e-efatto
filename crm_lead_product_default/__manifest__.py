# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'CRM lead product defaults',
    'version': '12.0.1.0.0',
    'category': 'Sales Management',
    'license': 'AGPL-3',
    'description': """
    Set default product type to stockable to product created from lead.
    Set product name to a code related to crm lead code.
    Set default category of product on crm lead product category. Admin user can set 
    a predefined value to crm.lead object, but this one can be changed by normal user.
    """,
    'author': "Sergio Corato",
    'website': 'https://efatto.it',
    'depends': [
        'crm_lead_code',
        'crm_lead_product',
    ],
    'data': [
        'views/crm_lead.xml',
        'views/crm_lead_line.xml',
    ],
    'installable': True,
}
