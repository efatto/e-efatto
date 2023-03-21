# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from .test_common import TestExcelImportExport
from odoo.tests.common import Form


class TestXLSXImportExport(TestExcelImportExport):

    @classmethod
    def setUpClass(cls):
        super(TestExcelImportExport, cls).setUpClass()

    def test_xlsx_export_import(self):
        """ Test Export Excel from Mrp Boms """
        # Create Mrp Boms
        self.setUpMrpBom()
        # ----------- EXPORT ---------------
        ctx = {'active_model': 'mrp.bom',
               'active_id': self.mrp_bom.id,
               'template_domain': [('res_model', '=', 'mrp.bom'),
                                   ('fname', '=', 'mrp_bom.xlsx'),
                                   ('gname', '=', False)], }
        f = Form(self.env['export.xlsx.wizard'].with_context(ctx))
        export_wizard = f.save()
        # Test whether it loads correct template
        self.assertEqual(export_wizard.template_id,
                         self.env.ref('excel_import_export_bom.'
                                      'mrp_bom_xlsx_template'))
        # Export excel
        export_wizard.action_export()
        self.assertTrue(export_wizard.data)
        self.export_file = export_wizard.data

        # ----------- IMPORT ---------------
        ctx = {'active_model': 'mrp.bom',
               'active_id': self.mrp_bom.id,
               'template_domain': [('res_model', '=', 'mrp.bom'),
                                   ('fname', '=', 'mrp_bom.xlsx'),
                                   ('gname', '=', False)],
               'template_context': {},
               }
        with Form(self.env['import.xlsx.wizard'].with_context(ctx)) as f:
            f.import_file = self.export_file
        import_wizard = f.save()
        # Test sample template
        import_wizard.get_import_sample()
        self.assertTrue(import_wizard.datas)
        # Test whether it loads correct template
        self.assertEqual(import_wizard.template_id,
                         self.env.ref('excel_import_export_bom.'
                                      'mrp_bom_xlsx_template'))
        # Import Excel
        import_wizard.action_import()
