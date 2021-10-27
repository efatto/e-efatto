# Copyright 2020-2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    @api.one
    def _process(self, cancel_backorder=False):
        super(StockBackorderConfirmation, self)._process(
            cancel_backorder=cancel_backorder)
        self.mapped('pick_ids.backorder_ids').write(dict(state='waiting'))


class Picking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def action_pack_operation_auto_fill(self):
        super(Picking, self).action_pack_operation_auto_fill()
        for op in self.mapped('move_line_ids'):
            if op.product_id.type == 'product':
                op.qty_done = op.move_id.whs_list_ids[0].qtamov

    @api.multi
    def action_done(self):
        # Set whs_list.qta equal to move quantity_done, to stop any possible error
        # from whs user, if not elaborated from whs, else raise an error
        for pick in self:
            # Check whs lists are not in Elaborato=3 as WHS is working on them? no
            # as only stato=4 is processed
            # Synchronize whs lists? no as only stato=4 is processed, which is no
            # more workable from WHS
            # stato == '3' the whs list is no more processable, so ignored
            if any(x.stato == '4' and x.qtamov != x.move_id.quantity_done
                   for x in pick.mapped('move_lines.whs_list_ids')):
                raise UserError(_('Trying to validate picking %s which is '
                                  'already elaborated on Whs with different qty.') %
                                pick.name)
            # stato == '3' is ok when qtamov is 0, as is no more processable (n.b. qty
            # in move is obviously moved as it is the same move linked to correct list)
            if any(x.stato == '3' and x.qtamov != 0
                   for x in pick.mapped('move_lines.whs_list_ids')):
                raise UserError(_('Trying to validate picking %s which is '
                                  'not processable in Odoo but elaborated on Whs.'
                                  ) % pick.name)
            if any(x.stato not in ('3', '4') and x.move_id.quantity_done != 0
                   for x in pick.mapped('move_lines.whs_list_ids')):
                raise UserError(_('Trying to validate picking %s which is '
                                  'not elaborated on Whs.') % pick.name)
            for move in pick.move_lines:
                for whs_list in move.whs_list_ids:
                    if whs_list.qtamov != move.quantity_done != 0:
                        whs_list.qtamov = move.quantity_done
                    if whs_list.qtamov == 0 == move.quantity_done:
                        # When transfer is completed, the rows that have 0 qty are
                        # deleted, so they are re-created where the system create the
                        # backorder.
                        # In WHS the rows are registered with Elaborato=4 when they
                        # are terminated, even for the total, partial or 0.
                        # In WHS the lists are all in Elaborato=3 when the user is
                        # working on the order, so it is not possible that them are
                        # presents here as only stato=4 is processable on Odoo,
                        # that equals to Elaborato=4
                        # Lists with stato=3 and quantity_done=0 are deleted here
                        location_id = pick.location_id.id
                        if pick.picking_type_id.code == 'incoming':
                            location_id = pick.location_dest_id.id
                        dbsource = self.env['base.external.dbsource'].search([
                            ('location_id', '=', location_id)
                        ])
                        if not dbsource:
                            # This location is not linked to WHS System
                            continue
                        whs_list.whs_unlink_lists(dbsource.id)
        super(Picking, self).action_done()
        return True

    @api.multi
    def action_confirm(self):
        res = super(Picking, self).action_confirm()
        if not self._context.get('not_create_whs_list', False):
            self.mapped('move_lines').create_whs_list()
            for pick in self:
                pick.state = 'waiting'
        return res

    @api.multi
    def action_assign(self):
        res = super(Picking, self).action_assign()
        moves = self.mapped('move_lines').filtered(
            lambda move: not move.whs_list_ids)
        moves.create_whs_list()
        for pick in moves.mapped('picking_id'):
            pick.state = 'waiting'
        return res

    @api.multi
    def unlink(self):
        self.cancel_whs_list(unlink=True)
        return super(Picking, self).unlink()

    @api.multi
    def action_cancel(self):
        self.cancel_whs_list()
        return super(Picking, self).action_cancel()

    @api.multi
    def cancel_whs_list(self, unlink=False):
        for pick in self:
            whs_list_ids = pick.mapped('move_lines.whs_list_ids')
            if whs_list_ids:
                if any([x.stato != '1' and x.qtamov != 0 for x in whs_list_ids]):
                    raise UserError(_('Some moves already elaborated from WHS!'))

                location_id = pick.location_id.id
                if pick.picking_type_id.code == 'incoming':
                    location_id = pick.location_dest_id.id
                dbsource = self.env['base.external.dbsource'].search([
                    ('location_id', '=', location_id)
                ])
                if not dbsource:
                    # This location is not linked to WHS System
                    continue
                if unlink:
                    whs_list_ids.whs_unlink_lists(dbsource.id)
                else:
                    whs_list_ids.whs_cancel_lists(dbsource.id)
        return True


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def create_whs_list(self):
        whsliste_obj = self.env['hyddemo.whs.liste']
        list_number = False
        riga = 0
        for move in self:
            pick = move.picking_id
            tipo = False
            location_id = pick.location_id.id
            if pick.picking_type_id.code == 'incoming':
                tipo = '2'
                location_id = pick.location_dest_id.id
            elif pick.picking_type_id.code == 'outgoing':
                tipo = '1'
            # ROADMAP check this part as it is duplicated in mrp.py and an MO creates
            # whs_list with that function
            if all([x in [
                          self.env.ref('mrp.route_warehouse0_manufacture'),
                          self.env.ref('stock.route_warehouse0_mto')
                          ]
                    for x in move.product_id.route_ids]):
                # Never create whs list for OUT or IN related to manufactured products,
                # only create MO.
                # The IN will be without whs_list_ids so freely validatable
                # as production is done.
                # Same for the OUT, that one will be based only on Odoo stock current
                # availability (user has to check this one is correct)
                if move.procure_method == 'make_to_order':
                    continue
            #

            dbsource = self.env['base.external.dbsource'].search([
                ('location_id', '=', location_id)
            ])
            if not dbsource:
                # This location is not linked to WHS System
                continue
            if pick.partner_id:
                ragsoc = pick.partner_id.name
                cliente = pick.partner_id.ref if pick.partner_id.ref else \
                    pick.partner_id.parent_id.ref if pick.partner_id.parent_id.ref \
                    else False
                indirizzo = pick.partner_id.street if pick.partner_id.street else False
                cap = pick.partner_id.zip if pick.partner_id.zip else False
                localita = pick.partner_id.city if pick.partner_id.city else False
                provincia = pick.partner_id.state_id.code if pick.partner_id.state_id \
                    else False
                nazione = pick.partner_id.country_id.name if pick.partner_id.country_id\
                    else False

            if tipo:
                # ROADMAP check phantom products that generates only out moves
                if move.state != 'cancel' and move.product_id.type == 'product' \
                    and (
                        (pick.picking_type_id.code == 'incoming'
                         and move.location_dest_id.id == location_id)
                        or
                        (pick.picking_type_id.code == 'outgoing'
                         and move.location_id.id == location_id)
                        ):
                    if move.whs_list_ids and any(
                            x.stato != '3' for x in move.whs_list_ids):
                        _logger.info(
                            'Ignored creation of WHS list %s as it '
                            'already exists and is processable!'
                            % str(
                                ['%s-%s' % (x.riga, x.num_lista)
                                 for x in move.whs_list_ids
                                 if x.stato != '3']
                            )
                        )
                        continue
                    if not list_number:
                        list_number = self.env['ir.sequence'].next_by_code(
                            'hyddemo.whs.liste')
                        riga = 0
                    riga += 1
                    customer = move.product_id.customer_ids.filtered(
                            lambda x: x.name == pick.partner_id.commercial_partner_id
                        )
                    whsliste_data = {
                        'stato': '1',
                        'tipo': tipo,
                        'num_lista': list_number,
                        'data_lista': fields.Datetime.now(),
                        'product_id': move.product_id.id,
                        'qta': move.product_qty,
                        'move_id': move.id,
                        'tipo_mov': 'move',
                        'riga': riga,
                        'client_order_ref': move.sale_line_id.order_id.client_order_ref,
                    }
                    if move.sale_line_id.product_id != move.product_id:
                        whsliste_data.update({
                            'parent_product_id': move.sale_line_id.product_id.id,
                        })
                    if customer:
                        whsliste_data.update({
                            'product_customer_code': customer[0].product_code,
                        })
                    if pick.origin:
                        whsliste_data['riferimento'] = pick.origin[:50]

                    # ROADMAP: set priority
                    # if move.procurement_id and move.procurement_id.sale_line_id:
                    #   whsliste_data['priorita'] = move.procurement_id.\
                    #       sale_line_id.order_id.priorita

                    if ragsoc:
                        whsliste_data['ragsoc'] = ragsoc[0:100]
                    if indirizzo:
                        whsliste_data['indirizzo'] = indirizzo[0:50]
                    if cliente:
                        whsliste_data['cliente'] = cliente.strip()[0:30]
                    if cap:
                        whsliste_data['cap'] = cap[0:5]
                    if localita:
                        whsliste_data['localita'] = localita[0:50]
                    if provincia:
                        whsliste_data['provincia'] = provincia[0:2]
                    if nazione:
                        whsliste_data['nazione'] = nazione[0:50]
                    whsliste_obj.create(whsliste_data)
                    move.state = 'waiting'
        return True


class Location(models.Model):
    _inherit = "stock.location"

    def should_bypass_reservation(self):
        self.ensure_one()
        res = super(Location, self).should_bypass_reservation()
        if self.env['base.external.dbsource'].search([
            ('location_id', '=', self.id)
        ]):
            res = True
        return res
