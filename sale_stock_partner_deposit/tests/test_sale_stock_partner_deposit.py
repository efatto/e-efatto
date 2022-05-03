# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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
        cls.product = cls.env.ref('product.product_product_25')
        cls.product.write({
            'seller_ids': [(6, 0, [supplierinfo.id])],
            'route_ids': [(6, 0, [
                cls.env.ref('stock.route_warehouse0_mto').id,
                cls.env.ref('purchase_stock.route_warehouse0_buy').id,
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

    @mute_logger(
        'odoo.models', 'odoo.models.unlink', 'odoo.addons.base.ir.ir_model'
    )
    def test_00_todo(self):
        generic_deposit_location = self.env['stock.location'].create([{
            'name': 'Generic deposit location',
            'usage': 'customer',
            'location_id': self.ref('stock.stock_location_customers'),
            'deposit_location': True,
        }])
        deposit_location = self.env['stock.location'].create([{
            'name': 'Deposit location for %s' % self.partner.name,
            'partner_id': self.partner.id,
            'usage': 'customer',
            'location_id': generic_deposit_location.id,
            'deposit_location': True,
        }])
        self.partner.property_stock_deposit = deposit_location
        picking_type_from_stock_to_deposit = self.env['stock.picking.type'].create([{
            'name': 'Delivery from stock to deposit',
            # needed to show customer on picking
            'code': 'outgoing',
            'sequence_id': self.env['ir.sequence'].create({
                'name': 'Deposit incoming sequence',
            }).id,
            'default_location_src_id': self.ref('stock.stock_location_stock'),
            # this will be change to partner deposit from onchange
            'default_location_dest_id': generic_deposit_location.id,
        }])
        picking_type_from_deposit_to_stock = self.env['stock.picking.type'].create([{
            'name': 'Delivery from deposit to stock',
            'code': 'incoming',
            'sequence_id': self.env['ir.sequence'].create({
                'name': 'Deposit outgoing sequence',
            }).id,
            # this will be changed to partner deposit by function
            'default_location_src_id': generic_deposit_location.id,
            'default_location_dest_id': self.ref('stock.stock_location_stock'),
        }])
        picking_type_from_deposit_to_partner = self.env['stock.picking.type'].create([{
            'name': 'Delivery from deposit to partner',
            'code': 'outgoing',
            'sequence_id': self.env['ir.sequence'].create({
                'name': 'Deposit outgoing sequence',
            }).id,
            # this will be changed to partner deposit by function
            'default_location_src_id': self.ref('stock.stock_location_stock'),
            'default_location_dest_id': self.ref('stock.stock_location_customers'),
        }])
        stock_location_route = self.env['stock.location.route'].create([{
            'name': 'Delivery from partner stock deposit to partner',
            'sale_selectable': True,
            'rule_ids': [
                (0, 0, {
                    'name': 'move from deposit to customer',
                    'action': 'pull',
                    'picking_type_id': picking_type_from_deposit_to_partner.id,
                    'location_src_id': generic_deposit_location.id,
                    'location_id': self.ref('stock.stock_location_customers'),
                    'use_partner_stock_deposit': True,
                    'auto': 'manual',
                })
            ]
        }])
        # send goods to deposit location
        picking_obj = self.env['stock.picking'].sudo(self.stock_user)
        vals = {
            'name': 'Delivery order to deposit',
            'partner_id': self.partner.id,
            'picking_type_id': picking_type_from_stock_to_deposit.id,
            'location_id': self.ref('stock.stock_location_stock'),
            'location_dest_id': generic_deposit_location.id,
            'move_lines': [(0, 0, {
                'name': '/',
                'product_id': self.product.id,
                'product_uom': self.product.uom_id.id,
                'product_uom_qty': 3.0,
            })],
        }
        pick_to_deposit = picking_obj.create(vals)
        # call the onchange to change dest location
        pick_to_deposit.onchange_picking_type()
        self.assertEqual(pick_to_deposit.location_dest_id, deposit_location)
        self.env['stock.quant']._update_available_quantity(
            self.product, pick_to_deposit.location_id, 3.0)
        pick_to_deposit.action_assign()
        pick_to_deposit.move_lines[0].move_line_ids[0].qty_done = 3.0
        pick_to_deposit.action_done()
        # - verificare la quantità di merce in c/deposito con il report per ubicazione,
        # v. https://github.com/OCA/stock-logistics-reporting/tree/12.0/
        # stock_report_quantity_by_location
        quants = self.env['stock.quant'].search([
            ('location_id', 'child_of', deposit_location.id)
        ])
        self.assertEqual(quants.product_id, self.product)
        self.assertAlmostEqual(quants.quantity, 3.0)
        # Return 1 product from deposit to stock
        vals1 = {
            'name': 'Delivery return from deposit',
            'partner_id': self.partner.id,
            'picking_type_id': picking_type_from_deposit_to_stock.id,
            'location_id': generic_deposit_location.id,
            'location_dest_id': self.ref('stock.stock_location_stock'),
            'move_lines': [(0, 0, {
                'name': '/',
                'product_id': self.product.id,
                'product_uom': self.product.uom_id.id,
                'product_uom_qty': 1.0,
            })],
        }
        pick_to_deposit = picking_obj.create(vals1)
        # call the onchange to change dest location
        pick_to_deposit.onchange_picking_type()
        self.assertEqual(pick_to_deposit.location_id, deposit_location)
        pick_to_deposit.action_assign()
        pick_to_deposit.move_lines[0].move_line_ids[0].qty_done = 1.0
        pick_to_deposit.action_done()
        quants2 = self.env['stock.quant'].search([
            ('location_id', 'child_of', deposit_location.id)
        ])
        self.assertEqual(quants2.product_id, self.product)
        self.assertAlmostEqual(quants2.quantity, 2.0)
        sale_order = self.env['sale.order'].sudo(self.stock_user).create({
            'partner_id': self.partner.id,
            'route_id': stock_location_route.id,
        })
        # Sell remaining 2 products in deposit
        self._create_sale_order_line(sale_order, self.product, 2.0)
        sale_order.action_confirm()
        picking = sale_order.picking_ids[0]
        self.assertEqual(picking.location_id, deposit_location)
        picking.action_assign()
        picking.move_lines[0].move_line_ids[0].qty_done = 2.0
        picking.action_done()
        quants1 = self.env['stock.quant'].search([
            ('location_id', 'child_of', deposit_location.id)
        ])
        self.assertEqual(quants1.product_id, self.product)
        self.assertAlmostEqual(quants1.quantity, 0.0)
        # possibile sviluppo: creare un automatismo per generare un Ordine di vendita
        #  dall'ubicazione del deposito)

        # - a fine anno creare un'inventario specifico per l'ubicazione per avere il
        #  dettaglio di quanto in deposito e per valorizzarlo come il resto del magazzin
