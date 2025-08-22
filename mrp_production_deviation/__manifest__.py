# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Production deviation info",
    "version": "14.0.1.0.0",
    "summary": "Show deviation of production",
    "license": "AGPL-3",
    "category": "Manufacturing",
    "author": "Sergio Corato",
    "website": "https://github.com/efatto/e-efatto",
    "depends": [
        "mrp_production_component_change",
        "mrp_production_expected_qty",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/mrp_production_deviation_report.xml",
        "views/mrp.xml",
    ],
    "installable": True,
}
