from base64 import b64decode
import json
import os
from odoo import models, api, fields, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

try:
    import xlrd
    from xlrd.xldate import xldate_as_datetime  # noqa
except (ImportError, IOError) as err:  # pragma: no cover
    _logger.error(err)


class WizardMrpBomImportXlsx(models.TransientModel):
    _name = "wizard.mrp.bom.import.xlsx"
    _description = 'Wizard MRP BOM line import Xlsx'

    data_file = fields.Binary("Bom File", required=True)
    filename = fields.Char()
    header = fields.Char()

    @api.model
    def parse_header(self, data_file):
        workbook = xlrd.open_workbook(
            file_contents=data_file
        )
        sheet = workbook.sheet_by_index(0)
        values = sheet.row_values(0)
        return [str(value) for value in values]

    @api.onchange('data_file')
    def _onchange_data_file(self):
        if not self.data_file:
            return
        header = self.parse_header(
            b64decode(self.data_file)
        )
        self.header = json.dumps(header)

    @api.model
    def parse_lines(self, data_file):
        workbook = xlrd.open_workbook(
            file_contents=data_file,
        )
        xlsx = (workbook, workbook.sheet_by_index(0),)
        if isinstance(xlsx, tuple):
            header = [str(value) for value in xlsx[1].row_values(0)]
        else:
            header = [value.strip() for value in next(xlsx)]
        default_code_column = header.index('default_code')
        quantity_column = header.index('quantity')
        uom_column = header.index('uom')

        if isinstance(xlsx, tuple):
            rows = range(1, xlsx[1].nrows)
        else:
            rows = xlsx

        lines = []
        for row in rows:
            if isinstance(xlsx, tuple):
                # book = xlsx[0]
                sheet = xlsx[1]
                values = []
                for col_index in range(sheet.row_len(row)):
                    # cell_type = sheet.cell_type(row, col_index)
                    cell_value = sheet.cell_value(row, col_index)
                    values.append(cell_value)
            else:
                values = list(row)
            line = {}
            default_code = values[default_code_column]
            quantity = values[quantity_column]
            uom = values[uom_column]
            if default_code is not None:
                line['default_code'] = default_code
            if quantity is not None:
                line['quantity'] = quantity
            if uom is not None:
                line['uom'] = uom
            lines.append(line)
        return lines

    @api.multi
    def import_xlsx(self):
        self.ensure_one()
        (filename, ext) = os.path.splitext(self.filename)
        if ext.replace('.', '') != 'xlsx':
            raise UserError(_('Only Xlsx supported!'))
        lines = self.parse_lines(b64decode(self.data_file))
        product_obj = self.env['product.product']
        uom_obj = self.env['uom.uom']
        bom_lines_vals = []
        for line in lines:
            product_id = product_obj.search([
                ('default_code', '=', line['default_code'])
            ])
            # This search is done only to check if user changed uom value, as it
            # depends on user lang, but export is made on source term, so it generally
            # fail.
            uom_id = uom_obj.search([
                ('name', '=', line['uom'])
            ])
            if not uom_id:
                # search by source term, the default exported lang
                uom_id = uom_obj.with_context(lang='en_EN').search([
                    ('name', '=', line['uom'])
                ])
            if product_id and uom_id and line['quantity']:
                bom_lines_vals.append([
                    0, 0, {
                        'product_id': product_id.id,
                        'uom_id': uom_id.id,
                        'quantity': line['quantity']
                    }
                ])
        bom_id = self.env.context['active_id']
        bom = self.env['mrp.bom'].browse(bom_id)
        bom.write({'bom_line_ids': [(5, )]})
        bom.write({
            'bom_line_ids': bom_lines_vals
        })
