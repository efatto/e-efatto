# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.tools import mute_logger
import time


@tagged("-standard", "test_wms")
class CommonConnectorWMS(TransactionCase):
    def setUp(self):
        super().setUp()
        self.dbsource_model = self.env["base.external.dbsource"]
        self.dest_location = self.env.ref('stock.stock_location_customers')
        self.src_location = self.env.ref('stock.stock_location_stock')
        self.wms_location = self.env["stock.location"].create({
            "name": "WMS Location (child of default internal location)",
            "location_id": self.src_location.id,
        })
        self.manufacture_location = self.env["stock.location"].search([
            ("usage", "=", "production")
        ], limit=1)[0]
        self.procurement_model = self.env['procurement.group']
        self.partner = self.env.ref('base.res_partner_2')
        # Create product with 11 on hand on WMS location and 5 in default Stock location
        # Odoo gets products from all internal locations in the warehouse by default
        self.product1 = self.env['product.product'].create([{
            'name': 'test product1',
            'default_code': 'PRODUCT1',
            'type': 'product',
        }])
        self.StockQuant = self.env['stock.quant']
        self.quant_product1 = self.StockQuant.create([{
            'product_id': self.product1.id,
            'location_id': self.wms_location.id,
            'quantity': 11.0,
        }])
        self.quant_product1 = self.StockQuant.create([{
            'product_id': self.product1.id,
            'location_id': self.src_location.id,
            'quantity': 5.0,
        }])
        # Create product with 8 on hand
        self.product2 = self.env['product.product'].create([{
            'name': 'test product2',
            'default_code': 'PRODUCT2',
            'type': 'product',
        }])
        self.quant_product2 = self.StockQuant.create([{
            'product_id': self.product2.id,
            'location_id': self.wms_location.id,
            'quantity': 8.0,
        }])
        # create product excluded from WMS with 10 on hand
        self.product_excluded = self.env['product.product'].create([{
            'name': 'test product excluded from WMS',
            'default_code': 'PRODUCT1',
            'type': 'product',
            'exclude_from_whs': True,
        }])
        self.quant_product_excluded = self.StockQuant.create([{
            'product_id': self.product_excluded.id,
            'location_id': self.src_location.id,
            'quantity': 10.0,
        }])
        # Large Cabinet, 250 on hand
        self.product3 = self.env.ref('product.product_product_6')
        # Drawer Black, 0 on hand
        self.product4 = self.env.ref('product.product_product_16')
        self.product5 = self.env.ref('product.product_product_20')
        self.product1.invoice_policy = 'order'
        self.product1.write({
            'customer_ids': [
                (0, 0, {
                    'name': self.partner.id,
                    'product_code': 'CUSTOMERCODE',
                    'product_name': 'Product customer name',
                })
            ]
        })
        self.product2.invoice_policy = 'order'

    def run_stock_procurement_scheduler(self):
        with mute_logger('odoo.addons.stock.models.procurement'):
            self.procurement_model.run_scheduler(True)
            time.sleep(30)
