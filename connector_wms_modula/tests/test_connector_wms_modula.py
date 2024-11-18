
from odoo.tests import tagged
from odoo.addons.connector_whs.tests.test_connector_wms import TestConnectorWhs


@tagged("-standard", "test_wms")
class TestConnectorWmsModula(TestConnectorWhs):
    @staticmethod
    def _get_connection_string():
        return "connection_wms_modula.txt"
