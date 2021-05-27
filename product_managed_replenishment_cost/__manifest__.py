# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Product Managed Replenishment Cost',
    'description': "Add costs from Customs Tariff and Country Group of Seller",
    'version': '12.0.1.0.0',
    'author': 'Sergio Corato',
    'category': 'Products',
    'depends': [
        'l10n_it_intrastat_tariff',
        'mrp_bom_cost',
        'product',
        'purchase_stock',
        'res_country_logistic_charge',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/replenishment_cost_security.xml',
        'views/product_product.xml',
        'views/product_template.xml',
        'views/replenishment_menu.xml',
    ],
    'installable': True,
}
