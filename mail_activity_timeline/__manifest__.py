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
        'mail_activity_partner',
        'mrp_production_calendar',
        'mrp_production_date_planned',
        'mrp_production_demo',
        'mrp_sale_info',
        'project',
        'web_timeline',
        'web_view_calendar_list',
    ],
    'data': [
        'data/mail_activity_type.xml',
        'views/mail_activity.xml',
        'views/mrp_workorder.xml',
        'views/mrp.xml',
    ],
    'installable': True,
}
