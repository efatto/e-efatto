# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Country group logistic charge',
    'version': '12.0.1.0.0',
    'author': 'Sergio Corato',
    'category': 'other',
    'depends': [
        'base',
    ],
    'data': [
        'views/res_country_group.xml',
    ],
    'description': "Add a percentage value of logistic costs to be paid when purchasing"
                   " from countries in a country group.",
    'installable': True,
}
