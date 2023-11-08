# Copyright 2021-2023 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Product Managed Replenishment Cost",
    "version": "14.0.1.0.1",
    "author": "Sergio Corato",
    "website": "https://github.com/sergiocorato/e-efatto",
    "category": "Products",
    "license": "AGPL-3",
    "depends": [
        "l10n_it_intrastat_tariff",
        "mrp",
        # "mrp_bom_cost",
        "product",
        "product_logistics_uom",
        "product_template_replenishment_cost",
        "purchase_discount",
        "purchase_stock",
        "res_country_logistic_charge",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/replenishment_cost_security.xml",
        "views/product_supplierinfo.xml",
        "views/replenishment_menu.xml",
        "views/product_product.xml",
        "views/product_template.xml",
    ],
    "installable": True,
}
