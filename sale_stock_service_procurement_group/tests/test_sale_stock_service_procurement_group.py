from odoo.tests.common import SavepointCase
from odoo.tools import mute_logger

class TestSaleStockPartnerDeposit(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.user_model = cls.env['res.users'].with_context(no_reset_password=True)
        cls.vendor = cls.env.ref('base.res_partner_3')
        supplierinfo = cls.env['product.supplierinfo'].create({
            'name': cls.vendor.id,
        })
        cls.service = cls.env['product.product'].create({
            'name': 'Service',
            'type': 'service',
            'standard_price': 100,
            'list_price': 250,
            'uom_id': cls.env.ref("uom.product_uom_unit").id,
            'uom_po_id': cls.env.ref("uom.product_uom_unit").id,
        })
        cls.product = cls.env.ref('product.product_product_25')
        cls.product.write({
            'seller_ids': [(6, 0, [supplierinfo.id])],
            'route_ids': [(6, 0, [
                cls.env.ref('stock.route_warehouse0_mto').id,
                # cls.env.ref('purchase_stock.route_warehouse0_buy').id,
            ])],
        })
        cls.partner = cls.env.ref('base.res_partner_2')
        cls.partner.customer = True
        cls.stock_user = cls.user_model.create([{
            'name': 'Demo user',
            'login': 'demo user',
            'groups_id': [
                (4, cls.env.ref('stock.group_adv_location').id),
                (4, cls.env.ref('sales_team.group_sale_salesman').id),
                (4, cls.env.ref('stock.group_stock_user').id),
            ]
        }])

    def _create_sale_order_line(self, order, product, qty):
        vals = {
            'order_id': order.id,
            'product_id': product.id,
            'product_uom_qty': qty,
            'price_unit': 100,
            }
        line = self.env['sale.order.line'].create(vals)
        line.product_id_change()
        line._convert_to_write(line._cache)
        return line

    def do_test(self, service_create_procurement_group=False):
        self.service.service_create_procurement_group = service_create_procurement_group
        self.sale_order = self.env['sale.order'].sudo(self.stock_user).create({
            'partner_id': self.partner.id,
        })
        self._create_sale_order_line(self.sale_order, self.service, 2.0)
        self.sale_order.action_confirm()
        

    @mute_logger(
        'odoo.models', 'odoo.models.unlink', 'odoo.addons.base.ir.ir_model'
    )
    def test_00_sale_order_without_procurement_group(self):
        self.do_test()
        self.assertFalse(self.sale_order.procurement_group_id)

    @mute_logger(
        'odoo.models', 'odoo.models.unlink', 'odoo.addons.base.ir.ir_model'
    )
    def test_01_sale_order_with_procurement_group(self):
        self.do_test(True)
        self.assertTrue(self.sale_order.procurement_group_id)
