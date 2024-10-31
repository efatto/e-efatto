# Copyright 2024 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Sale order disable onchange on product qty',
    'version': '12.0.1.0.1',
    'category': 'other',
    'author': 'Sergio Corato',
    'summary': 'Onchange on product qty no more modify unit price.',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'license': 'AGPL-3',
    'depends': [
        'sale_order_cost_recalculation',
    ],
    'data': [
    ],
    'installable': True,
}