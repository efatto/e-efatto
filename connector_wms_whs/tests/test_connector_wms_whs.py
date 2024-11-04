# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged
from odoo.addons.connector_whs.tests.test_connector_wms import TestConnectorWMS


@tagged("-standard", "test_wms")
class TestConnectorWmsModula(TestConnectorWMS):
    @staticmethod
    def _get_connection_string():
        return "connection_wms_whs.txt"
