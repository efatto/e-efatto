# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'MRP Production fix active move line',
    'version': '12.0.1.0.0',
    'development_status': 'Beta',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'summary': 'Fix a bug if the user click on active move line before selecting a '
               'product.',
    'depends': [
        'mrp',
    ],
    'data': [
        'views/mrp.xml',
    ],
    'installable': True,
}
