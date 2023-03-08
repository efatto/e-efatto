
from odoo.tests.common import SavepointCase
from odoo.tools.date_utils import date, relativedelta
from odoo.exceptions import ValidationError
import time


class TestProductManagedReplenishmentCost(SavepointCase):

    @staticmethod
    def _create_pricelist_item(pricelist, vals):
        item = pricelist.create(vals)
        item._convert_to_write(item._cache)
        return item

    def _create_purchase_order_line(self, order, product, qty, price):
        vals = {
            'order_id': order.id,
            'product_id': product.id,
            'product_qty': qty,
            'product_uom': product.uom_po_id.id,
            'price_unit': price,
            'name': product.name,
            'date_planned': date.today(),
        }
        line = self.env['purchase.order.line'].create(vals)
        line.onchange_product_id()
        line._convert_to_write(line._cache)
        line.price_unit = price
        return line

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.user_model = cls.env['res.users'].with_context(no_reset_password=True)
        cls.partner = cls.env.ref('base.res_partner_2')
        cls.vendor = cls.env.ref('base.res_partner_1')
        cls.vendor1 = cls.env.ref('base.res_partner_3')
        cls.vendor.country_id = cls.env.ref('base.it')
        mto = cls.env.ref('stock.route_warehouse0_mto')
        buy = cls.env.ref('purchase_stock.route_warehouse0_buy')
        cls.expense_categ = cls.env.ref('product.cat_expense')
        cls.child_expense_categ = cls.env['product.category'].create([{
            'name': 'Child expense category',
            'parent_id': cls.expense_categ.id,
        }])
        cls.child_expense_categ1 = cls.env['product.category'].create([{
            'name': 'Child expense category1',
            'parent_id': cls.expense_categ.id,
        }])
        cls.sub_child_expense_categ = cls.env['product.category'].create([{
            'name': 'Sub Child expense category',
            'parent_id': cls.child_expense_categ1.id,
        }])
        cls.sub_child_expense_categ1 = cls.env['product.category'].create([{
            'name': 'Sub Child expense category1',
            'parent_id': cls.child_expense_categ1.id,
        }])

        today = date.today()

        cls.product = cls.env['product.product'].create([{
            'name': 'Product with 1 seller',
            'standard_price': 50.0,
            'categ_id': cls.child_expense_categ.id,
            'seller_ids': [(0, 0, {
                'name': cls.vendor.id,
                'price': 20,
            })],
            'route_ids': [(6, 0, [buy.id, mto.id])],
            'purchase_ok': True,
        }])
        cls.product1 = cls.env['product.product'].create([{
            'name': 'Product without sellers',
            'categ_id': cls.sub_child_expense_categ.id,
            'route_ids': [(6, 0, [buy.id, mto.id])],
            'default_code': 'PWS',
            'purchase_ok': True,
        }])
        cls.product2 = cls.env['product.product'].create([{
            'name': 'Product with multiple sellers',
            'categ_id': cls.sub_child_expense_categ1.id,
            'route_ids': [(6, 0, [buy.id, mto.id])],
            'default_code': 'COMP2',
            'seller_ids': [
                (0, 0, {'name': cls.vendor.id, 'price': 3.5, 'date_end': today
                        + relativedelta(days=-60)}),
                (0, 0, {'name': cls.vendor.id, 'price': 4.4, 'date_start': today
                        + relativedelta(days=-59), 'date_end': today
                        + relativedelta(days=-30)}),
                (0, 0, {'name': cls.vendor1.id, 'price': 5.5}),
                (0, 0, {'name': cls.vendor.id, 'price': 6.6}),
            ],
            'purchase_ok': True,
        }])

        # Create pricelist for cost manipulation
        cls.pricelist = cls.env['product.pricelist'].create([{
            'name': 'Test pricelist for cost manipulation',
            'enable_supplierinfo_management': True,
        }])
        cls.pricelist_item = cls.env['product.pricelist.item']
        for vals in [
            {
                'pricelist_id': cls.pricelist.id,
                'applied_on': '2_product_category',
                'categ_id': cls.sub_child_expense_categ.id,
                'compute_price': 'formula',
                'base': 'standard_price',
                'price_discount': -40.0,
            },
            {
                'pricelist_id': cls.pricelist.id,
                'applied_on': '2_product_category',
                'categ_id': cls.sub_child_expense_categ.id,
                'compute_price': 'formula',
                'base': 'standard_price',
                'price_discount': -30.0,
            },
            {
                'pricelist_id': cls.pricelist.id,
                'applied_on': '2_product_category',
                'categ_id': cls.sub_child_expense_categ.id,
                'compute_price': 'formula',
                'base': 'list_price',
                'price_discount': -20.0,
            },
            {
                'pricelist_id': cls.pricelist.id,
                'applied_on': '2_product_category',
                'categ_id': cls.child_expense_categ.id,
                'compute_price': 'formula',
                'base': 'standard_price',
                'price_discount': -10.0,
            },
            {
                'pricelist_id': cls.pricelist.id,
                'applied_on': '2_product_category',
                'categ_id': cls.child_expense_categ.id,
                'compute_price': 'formula',
                'base': 'standard_price',
                'price_discount': -15.0,
                'date_start': today + relativedelta(days=-90),
                'date_end': today + relativedelta(days=-60),
            },
            {
                'pricelist_id': cls.pricelist.id,
                'applied_on': '2_product_category',
                'categ_id': cls.child_expense_categ.id,
                'compute_price': 'formula',
                'base': 'list_price',
                'price_discount': -20.0,
                'date_end': today + relativedelta(days=-91),
            },
        ]:
            cls._create_pricelist_item(cls.pricelist_item, vals=vals)
        cls.pricelist_parent = cls.env['product.pricelist'].create([{
            'name': 'Test Public Pricelist',
            'enable_supplierinfo_management': True,
        }])
        for vals in [
            {
                'pricelist_id': cls.pricelist_parent.id,
                'applied_on': '2_product_category',
                'compute_price': 'formula',
                'base': 'standard_price',
                'price_discount': -20.0,
            },
        ]:
            cls._create_pricelist_item(cls.pricelist_item, vals=vals)
        cls.pricelist_parent.item_ids.filtered(
            lambda x: x.applied_on == '3_global'
        ).write({
            'price_discount': -10.0,
            'compute_price': 'formula',
            'base': 'pricelist',
            'base_pricelist_id': cls.pricelist.id,
        })

    def test_00_check_pricelist(self):
        with self.assertRaises(ValidationError):
            vals = {
                'pricelist_id': self.pricelist.id,
                'applied_on': '1_product',
                'product_tmpl_id': self.product2.product_tmpl_id.id,
                'compute_price': 'fixed',
                'fixed_price': 150,
                'min_quantity': 1,
            }
            self._create_pricelist_item(self.pricelist_item, vals=vals)

    def test_01_today(self):
        today = date.today()
        day_check_validity = today
        with self.assertRaises(ValidationError):
            vals = {
                'pricelist_id': self.pricelist.id,
                'applied_on': '1_product',
                'product_tmpl_id': self.product2.product_tmpl_id.id,
                'compute_price': 'fixed',
                'fixed_price': 150,
                'min_quantity': 1,
            }
            self._create_pricelist_item(self.pricelist_item, vals=vals)
        self.execute_test(today, day_check_validity)

    def test_02_65_days_ago(self):
        today = date.today()
        day_check_validity = today + relativedelta(days=-65)
        self.execute_test(today, day_check_validity)

    def test_03_95_days_ago(self):
        today = date.today()
        day_check_validity = today + relativedelta(days=-95)
        self.execute_test(today, day_check_validity)

    def execute_test(self, today, day_check_validity):
        check = self.env['product.supplierinfo.check'].create([{
            'name': 'Test cost update',
            'product_ctg_ids': [(6, 0, self.child_expense_categ.ids)],
            'listprice_id': self.pricelist.id,
            'date_validity_supplierinfo': day_check_validity,
        }])
        self.assertAlmostEqual(self.product.managed_replenishment_cost, 0)
        check.check_products_supplierinfo()
        self.assertEqual(len(check.product_ids), 1)

        check.update_products_replenishment_cost()
        self.assertAlmostEqual(
            self.product.managed_replenishment_cost,
            20 * (
                1.1 if not check.date_validity_supplierinfo or
                (today + relativedelta(
                    days=-59)) <= check.date_validity_supplierinfo
                else 1.15 if (today + relativedelta(days=-60))
                >= check.date_validity_supplierinfo >= (
                    today + relativedelta(days=-90))
                else 1.2 if check.date_validity_supplierinfo
                <= (today + relativedelta(days=-91))
                else 1
            )
        )
        # todo verificare la possibile sovrapposizione di categorie prodotti
        #  es. se nel listino c'è la categoria padre e quella figlia in due diverse
        #  righe verrebbe applicata in successione (sovrascrivendo) o solo la prima?
        #  credo la seconda opzione
        #####
        # wait 2 seconds to ensure purchase date is later than seller price write date
        time.sleep(2)
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.vendor.id
        })
        self._create_purchase_order_line(purchase_order, self.product, 5.0, 77.55)
        purchase_order.button_approve()
        check.update_products_replenishment_cost()
        self.assertAlmostEqual(
            self.product.managed_replenishment_cost,
            77.55 * (
                1.1 if not check.date_validity_supplierinfo or
                (today + relativedelta(
                    days=-59)) <= check.date_validity_supplierinfo
                else 1.15 if (today + relativedelta(days=-60))
                >= check.date_validity_supplierinfo >= (
                    today + relativedelta(days=-90))
                else 1.2 if check.date_validity_supplierinfo
                <= (today + relativedelta(days=-91))
                else 1
            ),
            places=2
        )
