# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Connector Modula WMS",
    "version": "18.0.1.0.0",
    "category": "Warehouse Management",
    "license": "AGPL-3",
    "summary": """
    Add custom method to connect to Modula WMS.
    """,
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "depends": [
        "connector_whs",
    ],
    "data": [
        "data/cron.xml",
        "views/product_template.xml",
        "views/hyddemo_whs_liste.xml",
    ],
    "installable": True,
    "excludes": "connector_wms_whs",
    "external_dependencies": {"python": ["sqlalchemy==1.3.24"]},
}
