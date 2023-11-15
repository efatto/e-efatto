# Copyright 2020-2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# flake8: noqa: C901

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

EXTRA_PROCUREMENT_PRIORITIES = [('2', 'Very Urgent')]
# priority (priorità) da odoo14 i valori corrispondono (0='0', ecc.)
# odoo14: [('0', 'Normal'), ('1', 'Urgent')]
# odoo12: [('0', 'Not urgent'), ('1', 'Normal'), ('2', 'Urgent'), ('3', 'Very Urgent')]
# lo script di migrazione attuale traduce '1' a '0' (giusto), '2' a '1' (giusto) e
# '3' a '1' (sbagliato): todo correggere che '3' diventi '2', magari su un banale sql
# whs: # 0=Bassa; 1=Media; 2=Urgente

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    priority = fields.Selection(
        selection_add=EXTRA_PROCUREMENT_PRIORITIES)

    def action_pack_operation_auto_fill(self):
        super(Picking, self).action_pack_operation_auto_fill()
        for op in self.mapped("move_line_ids"):
            if op.product_id.type == "product" and op.move_id.whs_list_ids:
                op.qty_done = op.move_id.whs_list_ids[0].qtamov

    def _action_done(self):
        # Set whs_list.qta equal to move quantity_done, to stop any possible error
        # from whs user, if not elaborated from whs, else raise an error
        for pick in self:
            # Check whs lists are not in Elaborato=3 as WHS is working on them? no
            # as only stato=4 is processed
            # Synchronize whs lists? no as only stato=4 is processed, which is no
            # more workable from WHS
            # stato == '3' the whs list is no more processable, so ignored
            if any(
                x.stato == "4" and x.qtamov != x.move_id.quantity_done
                for x in pick.mapped("move_lines.whs_list_ids")
            ):
                raise UserError(
                    _(
                        "Trying to validate picking %s which is "
                        "already elaborated on Whs with different qty."
                    )
                    % pick.name
                )
            # stato == '3' is ok when qtamov is 0, as is no more processable (n.b. qty
            # in move is obviously moved as it is the same move linked to correct list)
            if any(
                x.stato == "3" and x.qtamov != 0
                for x in pick.mapped("move_lines.whs_list_ids")
            ):
                raise UserError(
                    _(
                        "Trying to validate picking %s which is "
                        "not processable in Odoo but elaborated on Whs."
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
                        "not elaborated on Whs."
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
                        # In WHS the rows are registered with Elaborato=4 when they
                        # are terminated, even for the total, partial or 0.
                        # In WHS the lists are all in Elaborato=3 when the user is
                        # working on the order, so it is not possible that them are
                        # presents here as only stato=4 is processable on Odoo,
                        # that equals to Elaborato=4
                        # Lists with stato=3 and quantity_done=0 are deleted here
                        location_id = pick.location_id.id
                        if pick.picking_type_id.code == "incoming":
                            location_id = pick.location_dest_id.id
                        dbsource = self.env["base.external.dbsource"].search(
                            [("location_id", "=", location_id)]
                        )
                        if not dbsource:
                            # This location is not linked to WHS System
                            continue
                        _logger.info(
                            "WHS LOG: unlink whs list in backorder process of "
                            "move %s" % move.name
                        )
                        whs_list.whs_unlink_lists(dbsource.id)
        super(Picking, self)._action_done()
        return True

    def create_whs_list(self):
        for picking in self:
            for move in picking.move_lines:
                if not move.whs_list_ids or all(
                    x.stato == "3" for x in move.whs_list_ids
                ):
                    move.create_whs_list()

    def action_confirm(self):
        res = super(Picking, self).action_confirm()
        self.create_whs_list()
        return res

    def action_assign(self):
        res = super(Picking, self).action_assign()
        self.create_whs_list()
        return res

    def unlink(self):
        self.cancel_whs_list(unlink=True)
        return super(Picking, self).unlink()

    def action_cancel(self):
        self.cancel_whs_list()
        return super(Picking, self).action_cancel()

    def cancel_whs_list(self, unlink=False):
        for pick in self:
            whs_list_ids = pick.mapped("move_lines.whs_list_ids")
            if whs_list_ids:
                if any([x.stato != "1" and x.qtamov != 0 for x in whs_list_ids]):
                    raise UserError(_("Some moves already elaborated from WHS!"))

                location = pick.location_id
                if pick.picking_type_id.code == "incoming":
                    location = pick.location_dest_id
                dbsource = self.env["base.external.dbsource"].search(
                    [("location_id", "=", location.id)]
                )
                if not dbsource:
                    _logger.info(
                        "WHS LOG: Location %s is not linked to WHS System"
                        % location.name
                    )
                    continue
                if unlink:
                    _logger.info("WHS LOG: unlink lists for picking %s" % pick.name)
                    whs_list_ids.whs_unlink_lists(dbsource.id)
                else:
                    whs_list_ids.whs_cancel_lists(dbsource.id)
        return True


class StockMove(models.Model):
    _inherit = "stock.move"

    priority = fields.Selection(
        selection_add=EXTRA_PROCUREMENT_PRIORITIES)
    whs_list_ids = fields.One2many(
        comodel_name="hyddemo.whs.liste", inverse_name="move_id", string="Whs Lists"
    )

    def _check_valid_whs_list(self):
        for move in self:
            valid_whs_list = move.whs_list_ids.filtered(lambda x: x.stato != "3")
            if valid_whs_list and not move.state == "done":
                if move.product_uom_qty != valid_whs_list.qta:
                    raise UserError(
                        _("Whs valid list exists and qty cannot be " "modified!")
                    )

    def write(self, vals):
        res = super().write(vals=vals)
        if (
            not self._context.get("do_not_propagate", False)
            and not self._context.get("do_not_unreserve", False)
            and not self._context.get("skip_overprocessed_check", False)
            and (vals.get("product_uom_qty") or vals.get("product_qty"))
        ):
            self._check_valid_whs_list()
        return res

    def _action_confirm(self, merge=True, merge_into=False):
        self.create_whs_list()
        return super()._action_confirm(merge, merge_into)

    def _action_assign(self):
        self.create_whs_list()
        return super()._action_assign()

    def create_whs_list(self):
        whsliste_obj = self.env["hyddemo.whs.liste"]
        list_number = False
        riga = 0
        for move in self:
            pick = move.picking_id
            tipo = False
            location_id = pick.location_id.id
            ragsoc = False
            indirizzo = False
            cliente = False
            cap = False
            localita = False
            provincia = False
            nazione = False
            if pick.picking_type_id.code == "incoming":
                tipo = "2"
                location_id = pick.location_dest_id.id
            elif pick.picking_type_id.code == "outgoing":
                tipo = "1"
            # ROADMAP check this part as it is duplicated in mrp.py and an MO creates
            # whs_list with that function
            if all(
                [
                    x
                    in [
                        self.env.ref("mrp.route_warehouse0_manufacture"),
                        self.env.ref("stock.route_warehouse0_mto"),
                    ]
                    for x in move.product_id.route_ids
                ]
            ):
                # Never create whs list for OUT or IN related to manufactured products,
                # only create MO.
                # The IN will be without whs_list_ids so freely validatable
                # as production is done.
                # Same for the OUT, that one will be based only on Odoo stock current
                # availability (user has to check this one is correct)
                if move.procure_method == "make_to_order":
                    continue
            #

            dbsource = self.env["base.external.dbsource"].search(
                [("location_id", "=", location_id)]
            )
            if not dbsource:
                # This location is not linked to WHS System
                continue
            if pick.partner_id:
                ragsoc = pick.partner_id.name
                cliente = (
                    pick.partner_id.ref
                    if pick.partner_id.ref
                    else pick.partner_id.parent_id.ref
                    if pick.partner_id.parent_id.ref
                    else False
                )
                indirizzo = pick.partner_id.street if pick.partner_id.street else False
                cap = pick.partner_id.zip if pick.partner_id.zip else False
                localita = pick.partner_id.city if pick.partner_id.city else False
                provincia = (
                    pick.partner_id.state_id.code if pick.partner_id.state_id else False
                )
                nazione = (
                    pick.partner_id.country_id.name
                    if pick.partner_id.country_id
                    else False
                )

            if tipo:
                # ROADMAP check phantom products that generates only out moves
                if (
                    move.state != "cancel"
                    and move.product_id.type == "product"
                    and (
                        (
                            pick.picking_type_id.code == "incoming"
                            and move.location_dest_id.id == location_id
                        )
                        or (
                            pick.picking_type_id.code == "outgoing"
                            and move.location_id.id == location_id
                        )
                    )
                ):
                    if move.whs_list_ids and any(
                        x.stato != "3" for x in move.whs_list_ids
                    ):
                        _logger.info(
                            "WHS LOG: Ignored creation of WHS list %s as it "
                            "already exists and is processable!"
                            % str(
                                [
                                    "%s-%s" % (x.riga, x.num_lista)
                                    for x in move.whs_list_ids
                                    if x.stato != "3"
                                ]
                            )
                        )
                        continue
                    if not list_number:
                        list_number = self.env["ir.sequence"].next_by_code(
                            "hyddemo.whs.liste"
                        )
                        riga = 0
                    riga += 1
                    customer = move.product_id.customer_ids.filtered(
                        lambda x: x.name == pick.partner_id.commercial_partner_id
                    )
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
                            }
                        )
                    if pick.origin:
                        whsliste_data["riferimento"] = pick.origin[:50]

                    if move.sale_line_id.priority:
                        whsliste_data["priorita"] = (
                            max([int(move.sale_line_id.priority), 0])
                        )
                    elif move.priority:
                        whsliste_data["priorita"] = (
                            max([int(move.priority), 0])
                        )

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
                    _logger.info(
                        "WHS LOG: create list with data:\n %s" % (str(whsliste_data))
                    )
        return True
