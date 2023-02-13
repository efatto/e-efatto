import logging
from odoo import models, _

_logger = logging.getLogger(__name__)


class BomXlsx(models.AbstractModel):
    _name = 'report.mrp_bom_export_import_xlsx.bom_xlsx'
    _inherit = 'report.mrp_flattened_bom_xlsx.flattened_bom_xlsx'

    def print_bom_lines(self, bom, requirements, sheet, row):
        i = row
        for product, total_qty in requirements.items():
            sheet.write(i, 0, bom.product_tmpl_id.name or '')
            sheet.write(i, 1, product.default_code or '')
            sheet.write(i, 2, product.display_name or '')
            sheet.write(i, 3, total_qty or 0.0)
            sheet.write(i, 4, product.uom_id.name or '')
            i += 1
        return i

    def generate_xlsx_report(self, workbook, data, objects):
        workbook.set_properties({
            'comments': 'Created with Python and XlsxWriter from Odoo 12.0'})
        sheet = workbook.add_worksheet(_('BOM'))
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)
        sheet.set_zoom(80)
        sheet.set_column(0, 0, 40)
        sheet.set_column(1, 2, 20)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 5, 20)
        title_style = workbook.add_format({'bold': True,
                                           'bg_color': '#FFFFCC',
                                           'bottom': 1})
        sheet_title = ['BOM product name',
                       'default_code',
                       'Product Name',
                       'quantity',
                       'uom',
                       ]
        sheet.set_row(0, None, None, {'collapsed': 1})
        sheet.write_row(0, 0, sheet_title, title_style)
        sheet.freeze_panes(2, 0)
        i = 1

        for o in objects:
            # We need to calculate the totals for the BoM qty and UoM:
            starting_factor = o.product_uom_id._compute_quantity(
                o.product_qty, o.product_tmpl_id.uom_id, round=False)
            totals = o._get_flattened_totals(factor=starting_factor)
            i = self.print_bom_lines(o, totals, sheet, i)
