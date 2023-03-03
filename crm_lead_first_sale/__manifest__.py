# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'CRM lead first sale days',
    'version': '12.0.1.0.0',
    'category': 'Sales Management',
    'license': 'AGPL-3',
    'summary': """
    Add a field with days to first sale of crm lead, computed on date_sent added on 
    sale order.
    """,
    'author': "Sergio Corato",
    'website': 'https://efatto.it',
    'depends': [
        'sale_crm',
    ],
    'data': [
        'views/crm_lead.xml',
        'views/sale.xml',
    ],
    'installable': True,
}
