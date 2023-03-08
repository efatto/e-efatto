# © 2015-2016 Akretion (http://www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Product Cost History',
    'version': '12.0.1.0.0',
    'category': 'Product',
    'license': 'AGPL-3',
    'summary': 'Add a button to show product cost history',
    'author': 'Akretion, Sergio Corato',
    'website': 'https://github.com/sergiocorato/e-efatto',
    'depends': ['product'],
    'data': [
        'security/product_security.xml',
        'views/product_price_history_view.xml',
        'views/product_template_view.xml',
    ],
    'installable': True,
}
