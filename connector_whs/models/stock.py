# Copyright 2020-2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# flake8: noqa: C901

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

EXTRA_PROCUREMENT_PRIORITIES = [("2", "Very Urgent")]
# priority (priorità) da odoo14 i valori corrispondono (0='0', ecc.)
# odoo14: [('0', 'Normal'), ('1', 'Urgent')]
# odoo12: [('0', 'Not urgent'), ('1', 'Normal'), ('2', 'Urgent'), ('3', 'Very Urgent')]
# lo script di migrazione attuale traduce '1' a '0' (giusto), '2' a '1' (giusto) e
# '3' a '1' (sbagliato): todo correggere che '3' diventi '2', magari su un banale sql
# whs: # 0=Bassa; 1=Media; 2=Urgente

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    priority = fields.Selection(selection_add=EXTRA_PROCUREMENT_PRIORITIES)

    def action_pack_operation_auto_fill(self):
        super(Picking, self).action_pack_operation_auto_fill()
        for op in self.mapped("move_line_ids"):
            if op.product_id.type == "product" and op.move_id.whs_list_ids:
                op.qty_done = op.move_id.whs_list_ids[0].qtamov

    def _action_done(self):
        # Set whs_list.qta equal to move quantity_done, to stop any possible error
        # from wms user, if not elaborated from wms, else raise an error
        for pick in self:
            # Check wms lists are not in Elaborato=3 as WMS is working on them? no
            # as only stato=4 is processed
            # Synchronize wms lists? no as only stato=4 is processed, which is no
            # more workable from WMS
            # stato == "3" the wms list is no more processable, so ignored
            if any(
                x.stato == "4" and x.qtamov != x.move_id.quantity_done
                for x in pick.mapped("move_lines.whs_list_ids")
            ):
                raise UserError(
                    _(
                        "Trying to validate picking %s which is "
                        "already elaborated on WMS with different qty."
                    )
                    % pick.name
                )
            # stato == "3" is ok when qtamov is 0, as is no more processable (n.b. qty
            # in move is obviously moved as it is the same move linked to correct list)
            if any(
                x.stato == "3" and x.qtamov != 0
                for x in pick.mapped("move_lines.whs_list_ids")
            ):
                raise UserError(
                    _(
                        "Trying to validate picking %s which is "
                        "not processable in Odoo but elaborated on WMS."
                    )
                    % pick.name
                )
            if any(
                x.stato not in ("3", "4") and x.move_id.quantity_done != 0
                for x in pick.mapped("move_lines.whs_list_ids")
            ):
                raise UserError(
                    _(
                        "Trying to validate picking %s which is "
                        "not elaborated on WMS."
                    )
                    % pick.name
                )
            for move in pick.move_lines:
                for whs_list in move.whs_list_ids:
                    if whs_list.qtamov != move.quantity_done != 0:
                        whs_list.qtamov = move.quantity_done
                    if whs_list.qtamov == 0 == move.quantity_done:
                        # When transfer is completed, the rows that have 0 qty are
                        # deleted, so they are re-created where the system create the
                        # backorder.
                        # In WMS the rows are registered with Elaborato=4 when they
                        # are terminated, even for the total, partial or 0.
                        # In WMS the lists are all in Elaborato=3 when the user is
                        # working on the order, so it is not possible that them are
                        # presents here as only stato=4 is processable on Odoo,
                        # that equals to Elaborato=4
                        # Lists with stato=3 and quantity_done=0 are deleted here
                        dbsource = self.env["base.external.dbsource"].search([
                            ("stock_picking_type_ids", "in", pick.picking_type_id.ids),
                            ("company_id", "=", pick.company_id.id),
                        ])
                        if not dbsource:
                            _logger.info(
                                "WMS LOG: Picking type %s not linked to WMS System in "
                                "action_done" %
                                pick.picking_type_id.name)
                            continue
                        _logger.info("WMS LOG: unlink wms list in backorder process of "
                                     "move %s" % move.name)
                        whs_list.unlink_lists(dbsource.id)
        super(Picking, self)._action_done()
        return True

    def picking_create_whs_list(self):
        for picking in self:
            picking.move_lines.filtered(
                lambda move_line: not move_line.whs_list_ids
                or all(x.stato == "3" for x in move_line.whs_list_ids)
            ).create_whs_list()

    def action_confirm(self):
        res = super(Picking, self).action_confirm()
        self.picking_create_whs_list()
        return res

    def action_assign(self):
        res = super(Picking, self).action_assign()
        self.picking_create_whs_list()
        return res

    def unlink(self):
        self.cancel_whs_list(unlink=True)
        return super(Picking, self).unlink()

    def action_cancel(self):
        self.cancel_whs_list()
        return super(Picking, self).action_cancel()

    def cancel_whs_list(self, unlink=False):
        for pick in self:
            whs_lists = pick.mapped("move_lines.whs_list_ids")
            if whs_lists:
                dbsource = self.env["base.external.dbsource"].search([
                    ("stock_picking_type_ids", "in", pick.picking_type_id.ids),
                    ("company_id", "=", pick.company_id.id),
                ])
                if not dbsource:
                    _logger.info(
                        "WMS LOG: Picking type %s not linked to WMS System in "
                        "cancel_whs_list" %
                        pick.picking_type_id.name)
                    continue
                if any([x.stato != "1" and x.qtamov != 0 for x in whs_lists]):
                    raise UserError(_("Some moves already elaborated from WMS!"))
                if unlink:
                    _logger.info("WMS LOG: unlink lists for picking %s" % pick.name)
                    whs_lists.unlink_lists(dbsource.id)
                else:
                    whs_lists.cancel_lists(dbsource.id)
        return True


class StockMove(models.Model):
    _inherit = "stock.move"

    priority = fields.Selection(selection_add=EXTRA_PROCUREMENT_PRIORITIES)
    whs_list_ids = fields.One2many(
        comodel_name="hyddemo.whs.liste",
        inverse_name="move_id",
        string="WMS Lists")
    exclude_from_wms = fields.Boolean(
        string="Eclude from WMS",
    )

    def _check_done_whs_list(self):
        if any(x.stato != "4" and x.qta for x in self.mapped("whs_list_ids")):
            raise UserError(_("Almost a WMS list is not in state 'Ricevuto Esito'!"))

    def _check_valid_whs_list(self):
        for move in self:
            valid_whs_list = move.whs_list_ids.filtered(lambda x: x.stato != "3")
            origin_moves_whs_list = move.mapped(
                "move_orig_ids.whs_list_ids"
            ).filtered(lambda x: x.stato != "3")
            if (valid_whs_list or origin_moves_whs_list) and not move.state == "done":
                if move.purchase_line_id and valid_whs_list.stato == "1":
                    # update whs_list as it is not yet sent to WHS
                    valid_whs_list.qta = move.product_uom_qty
                elif (
                    not move.purchase_line_id
                    and (
                        move.product_uom_qty != valid_whs_list.qta
                        or move.product_uom_qty != origin_moves_whs_list.qta
                    )
                ):
                    raise UserError(
                        _(
                            "WMS valid list exists and qty cannot be modified!\n"
                            "To proceed, create a new line with the additional "
                            "requested quantity."
                        )
                    )
                if move.quantity_done != valid_whs_list.qtamov:
                    raise UserError(
                        _(
                            "A WMS valid list exists and qty moved is different "
                            "from quantity done on move!\n"
                            "To proceed, align quantity done in move to the quantity "
                            "moved in WHS list."
                        )
                    )

    def write(self, vals):
        # this check is needed because qty can be changed in a sale order, wich trigger
        # the change in stock move, which must be forbidden because WHS list is already
        # created and sent to WHS. The user must create a new line.
        # TODO CHECK:
        #  this key does not exist anymore and seems unused
        #  not self._context.get("do_not_propagate", False)
        if not self._context.get("do_not_unreserve", False) and (
            vals.get("product_uom_qty") or vals.get("product_qty")
            or self._context.get("previous_product_uom_qty")
        ):
            res = super().write(vals)
            self._check_valid_whs_list()
            return res
        return super().write(vals)

    def _action_confirm(self, merge=True, merge_into=False):
        if self.env["base.external.dbsource"].search([
            ("location_id", "in", (
                self.mapped("location_dest_id") | self.mapped("location_id")
            ).ids),
        ]):
            move_to_create_whs_list = self
            for move in self:
                if merge and merge_into:
                    # this move will be deleted, so do not create a whs list
                    move_to_create_whs_list -= move
            move_to_create_whs_list.create_whs_list()
        return super()._action_confirm(merge, merge_into)

    @staticmethod
    def _set_priority(move, whsliste_data):
        # overridable method
        return whsliste_data

    def create_whs_list(self):
        if self.env.context.get("bypass_wms"):
            return True
        moves_todo = self.filtered(lambda x: not x.exclude_from_wms)
        whsliste_obj = self.env["hyddemo.whs.liste"]
        list_number = False
        for move in moves_todo.filtered(lambda x: not x.product_id.exclude_from_whs):
            # get existing active list_number to append new whslist
            list_numbers = list(
                set(
                    move.picking_id.move_lines.mapped("whs_list_ids")
                    .filtered(lambda x: x.stato != "3")
                    .mapped("num_lista")
                )
            )
            if list_numbers:
                if len(list_numbers) > 1:
                    raise UserError(
                        _("More than one list number found for picking %s:" "%s")
                        % (move.picking_id.name, "|".join(list_numbers))
                    )
                if len(list_numbers) == 1:
                    list_number = list_numbers[0]
            tipo = False
            ragsoc = False
            indirizzo = False
            cliente = False
            cap = False
            localita = False
            provincia = False
            nazione = False
            # ROADMAP check this part as it is duplicated in mrp.py and an MO creates
            # whs_list with that function
            if all(
                [
                    x in [
                        self.env.ref("mrp.route_warehouse0_manufacture"),
                        self.env.ref("stock.route_warehouse0_mto")
                    ]
                    for x in move.product_id.route_ids
                ]
            ):
                # Never create wms list for OUT or IN related to manufactured products,
                # only create MO.
                # The IN will be without whs_list_ids so freely validatable
                # as production is done.
                # Same for the OUT, that one will be based only on Odoo stock current
                # availability (user has to check this one is correct)
                if move.procure_method == "make_to_order":
                    continue

            dbsource = self.env["base.external.dbsource"].search([
                ("stock_picking_type_ids", "in", move.picking_type_id.ids),
                ("company_id", "=", move.company_id.id),
            ])
            if not dbsource:
                # Picking type is not linked to WMS System
                continue
            warehouse = move.picking_type_id.warehouse_id
            reception_steps = warehouse.reception_steps
            delivery_steps = warehouse.delivery_steps
            manufacture_steps = warehouse.manufacture_steps
            if (
                # reception two steps
                reception_steps == "two_steps" and
                move.location_id != warehouse.lot_stock_id and
                move.location_dest_id == warehouse.lot_stock_id
            ) or (
                # incoming product from production two steps
                manufacture_steps == "pbm" and
                move.location_id != warehouse.lot_stock_id and
                move.location_dest_id == warehouse.lot_stock_id
            ) or (
                # reception one step
                reception_steps == "one_step" and
                move.picking_type_id.code == "incoming"
            ) or (
                # incoming product from production one step
                manufacture_steps == "mrp_one_step" and
                move.picking_type_id.code == "mrp_operation"
            ):
                tipo = "2"
                # set Modula dest location if it`s an incoming transfer or a move from
                # input location to internal location (2 steps case)
                move.location_dest_id = dbsource.location_id
            elif (
                # delivery two steps
                delivery_steps == "pick_ship" and
                move.location_id in [warehouse.lot_stock_id, dbsource.location_id] and
                move.location_dest_id != warehouse.lot_stock_id
            ) or (
                # consumption of components two steps
                manufacture_steps == "pbm" and
                move.location_id in [warehouse.lot_stock_id, dbsource.location_id] and
                move.location_dest_id != warehouse.lot_stock_id
            ) or (
                # delivery one step
                delivery_steps == "ship_only" and
                move.picking_type_id.code == "outgoing"
            ) or (
                # consumption of components one step
                manufacture_steps == "mrp_one_step" and
                move.location_id in [warehouse.lot_stock_id, dbsource.location_id] and
                move.picking_type_id.code == "mrp_operation"
            ):
                tipo = "1"
                # set Modula source location if it`s an outgoing or consuming transfer
                move.location_id = dbsource.location_id
            if not tipo:
                # todo actively exclude moves not managed by WMS, except for production?
                if move.picking_type_id not in dbsource.stock_picking_type_ids:
                    continue
                if all(
                    x != dbsource.location_id for x in (
                        move.location_id | move.location_dest_id)
                ):
                    # none of move locations are enabled in WMS
                    continue
            partner_id = move.partner_id or move.move_orig_ids.picking_id.partner_id
            if partner_id:
                ragsoc = partner_id.name
                cliente = partner_id.ref if partner_id.ref else \
                    partner_id.parent_id.ref if partner_id.parent_id.ref else False
                indirizzo = partner_id.street if partner_id.street else False
                cap = partner_id.zip if partner_id.zip else False
                localita = partner_id.city if partner_id.city else False
                provincia = partner_id.state_id.code if partner_id.state_id else False
                nazione = partner_id.country_id.name if partner_id.country_id else False

            if tipo:
                # ROADMAP check phantom products that generates only out moves
                if (
                    move.state != "cancel" and move.product_id.type == "product"
                    and (
                        (tipo == "2" and move.location_dest_id == dbsource.location_id)
                        or
                        (tipo == "1" and move.location_id == dbsource.location_id)
                        )
                ):
                    if move.whs_list_ids and any(
                        x.stato != "3" for x in move.whs_list_ids
                    ):
                        _logger.info(
                            "WMS LOG: Ignored creation of WMS list %s as it "
                            "already exists and is processable!"
                            % str(
                                ["%s-%s" % (x.riga, x.num_lista)
                                 for x in move.whs_list_ids
                                 if x.stato != "3"]
                            )
                        )
                    continue
                if not list_number:
                    list_number = self.env["ir.sequence"].next_by_code(
                        "hyddemo.whs.liste"
                    )
                    riga = 0
                else:
                    riga = max(whsliste_obj.search([
                        ("num_lista", "=", list_number),
                    ]).mapped("riga"))
                riga += 1
                customer = partner_id and move.product_id.customer_ids.filtered(
                    lambda x: x.name == partner_id.commercial_partner_id
                ) or False
                whsliste_data = {
                    "stato": "1",
                    "tipo": tipo,
                    "num_lista": list_number,
                    "data_lista": fields.Datetime.now(),
                    "product_id": move.product_id.id,
                    "qta": move.product_qty,
                    "move_id": move.id,
                    "tipo_mov": "move",
                    "riga": riga,
                    "client_order_ref": move.sale_line_id.order_id.client_order_ref,
                }
                if move.sale_line_id.product_id != move.product_id:
                    whsliste_data.update(
                        {
                            "parent_product_id": move.sale_line_id.product_id.id,
                        }
                    )
                if customer:
                    whsliste_data.update(
                        {
                            "product_customer_code": customer[0].product_code,
                        })
                if move.origin:
                    whsliste_data["riferimento"] = move.origin[:50]

                whsliste_data = moves_todo._set_priority(move, whsliste_data)
                #
                # if move.sale_line_id.priority:
                #     whsliste_data["priorita"] = max(
                #         [int(move.sale_line_id.priority), 0]
                #     )
                # elif move.priority:
                #     whsliste_data["priorita"] = max([int(move.priority), 0])

                if ragsoc:
                    whsliste_data["ragsoc"] = ragsoc[0:100]
                if indirizzo:
                    whsliste_data["indirizzo"] = indirizzo[0:50]
                if cliente:
                    whsliste_data["cliente"] = cliente.strip()[0:30]
                if cap:
                    whsliste_data["cap"] = cap[0:5]
                if localita:
                    whsliste_data["localita"] = localita[0:50]
                if provincia:
                    whsliste_data["provincia"] = provincia[0:2]
                if nazione:
                    whsliste_data["nazione"] = nazione[0:50]
                whsliste_obj.create(whsliste_data)
                _logger.info("WMS LOG: create list with data:\n %s" % (
                    str(whsliste_data)
                ))
            else:
                raise UserError(
                    _("WMS LOG: list tipo not found for stock move ID %s") % move.id)
        return True
