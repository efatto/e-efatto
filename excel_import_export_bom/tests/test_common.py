# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo.tests.common import SingleTransactionCase


class TestExcelImportExport(SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestExcelImportExport, cls).setUpClass()

    @classmethod
    def setUpXLSXTemplate(cls):
        cls.template_obj = cls.env['xlsx.template']
        # Create xlsx.template using input_instruction
        input_instruction = {
            '__EXPORT__': {
                'mrp_bom': {
                    '_HEAD_': {
                        'A2': 'product_tmpl_id${value and value.barcode or value.default_code or value.name or ""}#{style=text}',  # noqa
                        'B2': 'product_qty${value or 0}#{style=number}',
                        'C2': 'product_uom_id.name${value or ""}#{style=text}',
                        'D2': 'routing_id.name${value or ""}#{style=text}',
                    },
                    'bom_line_ids': {
                        'E2': 'product_id.barcode${value or ""}#{style=text}',
                        'F2': 'product_qty${value or 0}#{style=number}',
                        'G2': 'product_uom_id.name${value or ""}#{style=text}',
                    }
                }
            },
            '__IMPORT__': {
                'mrp_bom': {
                    'bom_line_ids': {
                        'E2': 'product_id',
                        'F2': 'product_qty',
                        'G2': 'product_uom_id',
                    }
                }
            },
        }
        vals = {
            'res_model': 'mrp.bom',
            'fname': 'mrp_bom.xlsx',
            'name': 'Mrp Bom Template',
            'description': 'Sample Mrp Bom Template for testing',
            'input_instruction': str(input_instruction),
        }
        cls.sample_template = cls.template_obj.create(vals)

    @classmethod
    def setUpMrpBom(cls):
        cls.setUpPrepMrpBom()
        # Create a Mrp Bom
        product_line = {
            'name': cls.product_order.name,
            'product_id': cls.product_order.id,
            'product_uom_qty': 2,
            'product_uom': cls.product_order.uom_id.id,
            'price_unit': cls.product_order.list_price,
            'tax_id': False,
        }
        cls.mrp_bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.main_product.product_tmpl_id.id,
            'order_line': [(0, 0, product_line), (0, 0, product_line)],
        })

    @classmethod
    def setUpManyMrpBom(cls):
        cls.setUpPrepMrpBom()
        # Create many mrp bom
        product_line = {
            'name': cls.product_order.name,
            'product_id': cls.product_order.id,
            'product_uom_qty': 2,
            'product_uom': cls.product_order.uom_id.id,
            'price_unit': cls.product_order.list_price,
            'tax_id': False,
        }
        for i in range(10):
            cls.env['mrp.bom'].create({
                'product_tmpl_id': cls.main_product.product_tmpl_id.id,
                'order_line': [(0, 0, product_line), (0, 0, product_line)],
            })

    @classmethod
    def setUpPrepMrpBom(cls):
        uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.main_product = cls.env['product.product'].create({
            'name': "Main Product",
            'standard_price': 235.0,
            'list_price': 280.0,
            'type': 'product',
            'uom_id': uom_unit.id,
            'uom_po_id': uom_unit.id,
            'invoice_policy': 'order',
            'expense_policy': 'no',
            'default_code': 'MAIN_PROD',
            'service_type': 'manual',
            'taxes_id': False,
        })
        cls.product_order = cls.env['product.product'].create({
            'name': "Test Product",
            'standard_price': 235.0,
            'list_price': 280.0,
            'type': 'consu',
            'uom_id': uom_unit.id,
            'uom_po_id': uom_unit.id,
            'invoice_policy': 'order',
            'expense_policy': 'no',
            'default_code': 'PROD_ORDER',
            'service_type': 'manual',
            'taxes_id': False,
        })
