# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Country group purchase margin',
    'version': '12.0.1.0.0',
    'author': 'Sergio Corato',
    'category': 'other',
    'depends': [
        'base',
    ],
    'data': [
        'views/res_country_group.xml',
    ],
    'description': "Add a percentage value of cost sustained when purchasing from "
                   "countries in country groups.",
    'installable': True,
}
