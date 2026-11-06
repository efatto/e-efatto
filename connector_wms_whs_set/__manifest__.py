# Copyright 2025 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Connector WMS and Production Set",
    "version": "18.0.1.0.0",
    "category": "Warehouse Management",
    "license": "AGPL-3",
    "development_status": "Alpha",
    "summary": """
    Glue module when connector to WMS and Production Set are intalled.
    """,
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "depends": [
        "connector_whs",
        "connector_wms_whs",
        "mrp_production_set",
    ],
    "data": [
        "views/mrp_production_set.xml",
    ],
    "installable": True,
    "auto_install": True,
}
