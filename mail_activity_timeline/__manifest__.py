# Copyright 2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Resource Planner Timeline',
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'category': 'Mail',
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'description': 'Use mail activity to plan resources.',
    'depends': [
        'mail_activity_board',
        'mrp_production_calendar',
        'mrp_production_demo',
        'mrp_sale_info',
        'project',
        'web_timeline',
    ],
    'data': [
        'data/mail_activity_type.xml',
        'views/mail_activity.xml',
        'views/mrp_workorder.xml',
    ],
    'installable': True,
}
