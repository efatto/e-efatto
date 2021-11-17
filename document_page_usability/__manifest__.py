# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': "Document Page Usability",
    'summary': """
        Remove required from fields: Draft name and Draft summary""",

    'description': """
        These fields can be left void.
    """,
    'author': "Sergio Corato",
    'website': "https://efatto.it",
    'category': 'Uncategorized',
    'version': '12.0.1.0.0',
    'depends': ['document_page'],
    'data': [
        'views/views.xml',
    ],
}