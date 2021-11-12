# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Product Managed Replenishment Cost',
    'version': '12.0.1.0.2',
    'author': 'Sergio Corato',
    'category': 'Products',
    'depends': [
        'l10n_it_intrastat_tariff',
        'mrp_bom_cost',
        'product_template_replenishment_cost',
        'purchase_discount',
        'purchase_stock',
        'res_country_logistic_charge',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/replenishment_cost_security.xml',
        'views/product_supplierinfo.xml',
        'views/replenishment_menu.xml',
    ],
    'installable': True,
}
