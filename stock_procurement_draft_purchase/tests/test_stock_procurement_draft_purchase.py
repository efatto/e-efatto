
from odoo.tests.common import SavepointCase
from odoo.tools import mute_logger


class StockProcurementDraftPurchase(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.user_model = cls.env['res.users'].with_context(no_reset_password=True)
        cls.product = cls.env.ref('product.product_product_1')

    @mute_logger(
        'odoo.models', 'odoo.models.unlink', 'odoo.addons.base.ir.ir_model'
    )
    def test_00_procurement(self):
        # TODO procurement rules have to run normally except if there are already
        #  created RdP by op that reaches the minimum qty
        pass
