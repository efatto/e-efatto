# Copyright 2019 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from odoo import _, fields, models
from odoo.fields import first
from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)


def _execute_onchanges(records, field_name):
    """Helper methods that executes all onchanges associated to a field."""
    for onchange in records._onchange_methods.get(field_name, []):
        for record in records:
            record._origin = record.env['stock.move']
            onchange(record)


class WizStockBarcodesReadMrp(models.TransientModel):
    _inherit = 'wiz.stock.barcodes.read'
    _name = 'wiz.stock.barcodes.read.mrp'
    _description = 'Wizard to read barcode on mrp'

    mrp_id = fields.Many2one(
        comodel_name='mrp.production',
        string='Production Order',
        readonly=True,
    )
    mrp_product_qty = fields.Float(
        string='Component quantities',
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True,
    )
    produced_lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Produced lot',
    )
    finished_lot_ids = fields.Many2many(
        comodel_name='stock.production.lot',
        string='Finished lots',
        readonly=True,
    )

    def name_get(self):
        return [
            (rec.id, '{} - {} - {}'.format(
                _('Barcode reader'),
                rec.mrp_id.name, self.env.user.name)) for rec in self]

    def action_done(self):
        if self.check_done_conditions():
            res = self._process_mrp_order_line()
            if res:
                self._add_read_log(res)

    def action_manual_entry(self):
        result = super().action_manual_entry()
        if result:
            self.action_done()
        return result

    def prepare_mrp_order_line_values(self, product_id=False):
        if not product_id:
            self._set_messagge_info(
                'not_found', _('Product not found'))
            return
        return {
            'raw_material_production_id': self.mrp_id.id,
            'product_id': product_id.id,
            'product_uom': product_id.uom_id.id,
            'name': product_id.display_name,
            'state': 'draft',
            'location_id': self.mrp_id.location_src_id.id,
            'location_dest_id': self.mrp_id.location_dest_id.id,
            'move_line_ids': [
                (0, 0, {
                    'product_uom_qty': 0,
                    'product_uom_id': product_id.uom_id.id,
                    'qty_done': 1,  # default to 1 as if > 1 write on existing move line
                    'production_id': self.mrp_id.id,
                    # 'workorder_id': self.id,
                    'product_id': product_id.id,
                    'done_wo': True,
                    'location_id': self.mrp_id.location_src_id.id,
                    'location_dest_id': self.mrp_id.location_dest_id.id,
                    'lot_id': self.lot_id.id,
                    'lot_name': self.lot_id.name,
                    'lot_produced_id': self.produced_lot_id.id,
                })
            ]
        }

    def process_barcode(self, barcode):
        """ override inherited function to use for mrp order """
        self._set_messagge_info('success', _('Barcode read correctly'))
        domain = self._barcode_domain(barcode)

        product = self.env['product.product'].search(domain)
        if product:
            if len(product) > 1:
                self._set_messagge_info(
                    'more_match', _('More than one product found'))
                return
            self.action_product_scaned_post(product)
            self.action_done()
            return

        if self.env.user.has_group('stock.group_production_lot'):
            lot_domain = [('name', '=', barcode)]
            if self.product_id:
                lot_domain.append(('product_id', '=', self.product_id.id))
            lot = self.env['stock.production.lot'].search(lot_domain)
            if len(lot) == 1:
                self.product_id = lot.product_id
            if not lot:
                produced_lot_ids = self.mrp_id.mapped('finished_move_line_ids.lot_id')
                if produced_lot_ids:
                    produced_lot = self.env['stock.production.lot'].search(
                        [('name', '=', barcode)])
                    if len(produced_lot) == 1:
                        self.lot_produced_id = produced_lot
                        self.action_done()
                        return
            if lot:
                self.action_lot_scaned_post(lot)
                self.action_done()
                return

        self._set_messagge_info('not_found', _('Barcode not found'))

    def _process_mrp_order_line(self):
        StockMove = self.env['stock.move']
        product_qty = self.product_qty
        stock_move_lines_dict = {}
        vals = {}
        if self.product_id:
            stock_move_product_lines = self.mrp_id.move_raw_ids.filtered(
                lambda x: x.product_id == self.product_id)
            if stock_move_product_lines and not self.lot_id:
                # write on first existing stock.move.line if lot is not set
                line = stock_move_product_lines[:1]
                # if move line exists and there is one without produced lot or with
                # the same produced lot, write on it
                if line.move_line_ids and \
                        not line.mapped('move_line_ids.lot_produced_id') \
                        or self.produced_lot_id in line.mapped(
                            'move_line_ids.lot_produced_id'):
                    if self.produced_lot_id in line.mapped(
                            'move_line_ids.lot_produced_id'):
                        move_line = line.move_line_ids.filtered(
                            lambda x: x.lot_produced_id == self.produced_lot_id
                        )[0]
                        move_line.write({
                            'qty_done': move_line.qty_done + product_qty,
                        })
                    else:
                        move_line = line.move_line_ids[0]
                        move_line.write({
                            'qty_done': move_line.qty_done + product_qty,
                            'lot_produced_id': self.produced_lot_id.id,
                        })
                else:
                    line.write({'move_line_ids': [
                        (0, 0, {
                            'product_uom_qty': 0,
                            'product_uom_id': self.product_id.uom_id.id,
                            'qty_done': product_qty,
                            'production_id': self.mrp_id.id,
                            # 'workorder_id': self.id,
                            'product_id': self.product_id.id,
                            'done_wo': True,
                            'location_id': self.mrp_id.location_src_id.id,
                            'location_dest_id': self.mrp_id.location_dest_id.id,
                            'lot_id': self.lot_id.id,
                            'lot_name': self.lot_id.name,
                            'lot_produced_id': self.produced_lot_id.id,
                        })
                    ]})
                # recompute all onchange fields
                # line.write({'product_uom_qty': line.product_uom_qty + product_qty})
                # _execute_onchanges(line, 'product_uom_qty')
                stock_move_lines_dict[line.id] = product_qty
                return stock_move_lines_dict
            # create a new stock.move.line if not exists or lot is set
            vals = self.prepare_mrp_order_line_values(product_id=self.product_id)

        if not vals:
            self._set_messagge_info(
                'not_found', _('Product  not found'))
            return
        line = StockMove.new(vals)
        # recompute all onchange fields
        _execute_onchanges(line, 'product_id')
        line.update({'product_uom_qty': product_qty})
        _execute_onchanges(line, 'product_uom_qty')
        stock_move_data = line._convert_to_write(line._cache)
        if self.mrp_id.move_raw_ids:
            stock_move_data['sequence'] = max(
                self.mapped('mrp_id.move_raw_ids.sequence') or [0]) + 1
        stock_move = StockMove.create(stock_move_data)
        stock_move_lines_dict[stock_move.id] = product_qty
        return stock_move_lines_dict

    def check_done_conditions(self):
        res = super().check_done_conditions()
        return res

    def _prepare_scan_log_values(self, log_detail=False):
        # Store in read log line each line added with the quantities assigned
        vals = super()._prepare_scan_log_values(log_detail=log_detail)
        vals['mrp_id'] = self.mrp_id.id
        vals['produced_lot_id'] = self.produced_lot_id.id
        if log_detail:
            vals['log_line_ids'] = [(0, 0, {
                'stock_move_id': x[0],
                'product_qty': x[1],
            }) for x in log_detail.items()]
        return vals

    def remove_scanning_log(self, scanning_log):
        for log in scanning_log:
            #todo remove qty from stock_move_id.move_line_ids
            for log_scan_line in log.log_line_ids:
                qty = (log_scan_line.stock_move_id.product_uom_qty -
                       log_scan_line.product_qty)
                log_scan_line.stock_move_id.product_uom_qty = max(qty, 0.0)
            self.stock_product_qty = sum(log.log_line_ids.mapped(
                'stock_move_id.product_uom_qty'))
            log.unlink()

    def action_undo_last_scan(self):
        res = super().action_undo_last_scan()
        log_scan = first(self.scan_log_ids.filtered(
            lambda x: x.create_uid == self.env.user))
        self.remove_scanning_log(log_scan)
        return res


class StockBarcodesReadLogLine(models.Model):
    _inherit = 'stock.barcodes.read.log.line'

    stock_move_id = fields.Many2one(
        comodel_name='stock.move',
        string='Stock move',
        readonly=True,
    )
