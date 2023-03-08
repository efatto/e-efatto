# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Production Group Lines By Product',
    'summary': 'Add ability to group lines with same product',
    'version': '12.0.1.0.1',
    'category': 'MRP',
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'license': 'AGPL-3',
    'maintainers': ['sergiocorato'],
    'depends': ['mrp_production_demo'],
    'data': [
        'wizard/production_group_line_wizard.xml',
        'views/mrp_production.xml',
    ],
    'installable': True,
}
