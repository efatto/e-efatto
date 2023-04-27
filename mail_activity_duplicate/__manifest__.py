# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Mail activity duplicate INCLUSO IN mail_activity_timeline',
    'version': '12.0.1.0.0',
    'category': 'Mail',
    'license': 'AGPL-3',
    'summary': """
    Add a button to duplicate activity.
    """,
    'author': "Sergio Corato",
    'website': 'https://github.com/sergiocorato/e-efatto',
    'depends': [
        'mail',
    ],
    'data': [
        'views/mail_activity.xml',
    ],
    'installable': False,
}
