# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from ast import literal_eval
from .test_common import TestExcelImportExport


class TestXLSXTemplate(TestExcelImportExport):

    @classmethod
    def setUpClass(cls):
        super(TestExcelImportExport, cls).setUpClass()

    def test_xlsx_template(self):
        """ Test XLSX Template input and output instruction """
        self.setUpXLSXTemplate()
        instruction_dict = literal_eval(self.sample_template.instruction)
        self.assertDictEqual(
            instruction_dict,
            {
                '__EXPORT__': {
                    'mrp_bom': {
                        '_HEAD_': {
                            'A2': 'product_tmpl_id${value and value.barcode or value.default_code or value.name or ""}#{style=text}#??',  # noqa
                            'B2': 'product_qty${value or 0}#{style=number}#??',
                            'C2': 'product_uom_id.name${value or ""}#{style=text}#??',
                            'D2': 'routing_id.name${value or ""}#{style=text}#??',
                        },
                        'bom_line_ids': {
                            'E2': 'product_id.barcode${value or ""}#{style=text}#??',
                            'F2': 'product_qty${value or 0}#{style=number}#??',
                            'G2': 'product_uom_id.name${value or ""}#{style=text}#??',
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
                '__POST_IMPORT__': False
            }
        )
        # Finally load excel file into this new template
        self.assertFalse(self.sample_template.datas)  # Not yet loaded
        self.template_obj.load_xlsx_template([self.sample_template.id],
                                             addon='excel_import_export_bom')
        self.assertTrue(self.sample_template.datas)  # Loaded successfully
