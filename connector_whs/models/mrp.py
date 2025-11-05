# Copyright 2013 Maryam Noorbakhsh creativiquadrati snc
# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# flake8: noqa: C901
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    sent_to_whs = fields.Boolean(
        string="Sent to WHS",
        compute="_compute_sent_to_whs",
        store=True,
    )
    state = fields.Selection(
        selection_add=[("consumed", "Consumed"), ("done",)],
        ondelete={"consumed": lambda r: r.write({"state": "progress"})},
        help=" * Draft: The MO is not confirmed yet.\n"
        " * Confirmed: The MO is confirmed, the stock rules and the reordering of "
        "the components are trigerred.\n"
        " * In Progress: The production has started (on the MO or on the WO).\n"
        " * To Close: The production is done, the MO has to be closed.\n"
        " * Consumed: The production is in progress, raw components has been "
        "moved from stock to production area.\n"
        " * Done: The MO is closed, the stock moves are posted. \n"
        " * Cancelled: The MO has been cancelled, can't be confirmed anymore.",
    )
    is_consumable = fields.Boolean(
        compute="_compute_is_consumable",
        store=True,
    )
    moves_to_do_ids = fields.Many2many(
        comodel_name="stock.move",
        string="Technical field to store moves to do in consume workflow",
    )
    bom_type = fields.Selection(
        related="bom_id.type",
        string="BOM Type",
    )

    @api.depends(
        "move_raw_ids.whs_list_ids",
        "move_finished_ids.whs_list_ids",
        "product_id.route_ids",
    )
    def _compute_sent_to_whs(self):
        for production in self.filtered(lambda mo: mo.state not in ["done", "cancel"]):
            moves = production.move_raw_ids
            is_two_steps = bool(
                "pbm" in moves.mapped("picking_type_id.warehouse_id.manufacture_steps")
            )
            if (
                production.picking_type_id.warehouse_id.mto_pull_id.route_id
                not in production.product_id.route_ids
            ):
                moves |= production.move_finished_ids
            production.sent_to_whs = is_two_steps or all(
                x.whs_list_ids
                and not all(whs_list.stato == "3" for whs_list in x.whs_list_ids)
                for x in moves.filtered(
                    lambda move: move.state not in ["done", "cancel"]
                    and move.product_uom_qty > 0
                )
            )
        for production in self.filtered(lambda mo: mo.state in ["done", "cancel"]):
            production.sent_to_whs = False

    @api.depends("product_qty", "qty_producing", "state")
    def _compute_is_consumable(self):
        for production in self:
            production.is_consumable = bool(
                production.product_qty == production.qty_producing
                and not production.state == "consumed"
            )

    def action_cancel(self):
        res = super().action_cancel()
        for production in self:
            whs_list_ids = (
                production.move_raw_ids | production.move_finished_ids
            ).mapped("whs_list_ids")
            if any([x.stato != "1" and x.qtamov != 0 for x in whs_list_ids]):
                raise UserError(_("Some moves already elaborated from WMS!"))
            for whs_list_id in whs_list_ids:
                location = (
                    whs_list_id.move_id.location_dest_id
                    if whs_list_id.tipo_mov == "mrpin"
                    else whs_list_id.move_id.location_id
                )
                dbsource = self.env["base.external.dbsource"].search(
                    [("location_id", "=", location.id)]
                )
                if not dbsource:
                    _logger.info(
                        "WMS LOG: Location %s is not linked to WMS System"
                        % location.name
                    )
                    continue
                _logger.info(
                    "WMS LOG: unlink lists for product %s of production %s"
                    % (whs_list_id.move_id.product_id.name, production.name)
                )
                whs_list_id.whs_unlink_lists(dbsource.id)
        return res

    def button_consume(self):
        self._button_mark_done_sanity_checks()
        for production in self:
            if (
                production.bom_id.type != "subcontract"
                and not production.sent_to_whs
                and production.state
                not in [
                    "done",
                    "cancel",
                ]
            ):
                raise UserError(
                    _("Production %s has not been sent to WHS!") % production.name
                )
            production.move_raw_ids._check_done_whs_list()
            if production.state == "progress":
                moves_to_do = production.move_raw_ids.filtered(
                    lambda x: x.state not in ("done", "cancel")
                )
                for move in moves_to_do.filtered(
                    lambda m: m.product_qty == 0.0 and m.quantity_done > 0
                ):
                    move.product_uom_qty = move.quantity_done
                # MRP do not merge move, catch the result of _action_done
                # to get extra moves.
                moves_to_do = moves_to_do._action_done()
                production._cal_price(moves_to_do)
                production.action_assign()
                production.moves_to_do_ids = [(6, 0, moves_to_do.ids)]
            production.write({"state": "consumed"})

    def button_mark_done(self):
        for production in self:
            if (
                not config["test_enable"] or self.env.context.get("test_connector_whs")
            ) and (
                not production.sent_to_whs
                and production.bom_id.type != "subcontract"
                and production.state
                not in [
                    "done",
                    "cancel",
                ]
            ):
                raise UserError(
                    _("Production %s has not been sent to WHS!") % production.name
                )
            (
                production.move_raw_ids | production.move_finished_ids
            )._check_done_whs_list()
            if production.state == "consumed":
                production.write({"state": "progress"})
        res = super().button_mark_done()
        for production in self:
            if not production.move_finished_ids.move_line_ids.consume_line_ids:
                production.move_finished_ids.move_line_ids.consume_line_ids = [
                    (6, 0, production.moves_to_do_ids.mapped("move_line_ids").ids)
                ]
                production.moves_to_do_ids = [(5,)]
        return res

    def button_send_to_whs(self):
        self._generate_whs()
        self._compute_sent_to_whs()

    @api.depends(
        "move_raw_ids.state",
        "move_raw_ids.quantity_done",
        "move_finished_ids.state",
        "workorder_ids",
        "workorder_ids.state",
        "product_qty",
        "qty_producing",
    )
    def _compute_state(self):
        # replace 'to_close' state with 'progress' to simplify flow
        super()._compute_state()
        for production in self:
            if production.state == "to_close":
                production.state = "progress"

    def _post_inventory(self, cancel_backorder=False):
        (self.move_raw_ids | self.move_finished_ids)._check_done_whs_list()
        res = super()._post_inventory(cancel_backorder=cancel_backorder)
        return res

    def _get_tipo(self, is_custom=False):
        # "11" if manufacturing but "12" if production_set
        return "11" if is_custom else "1"

    def _get_num_lista(self):
        return self.env["ir.sequence"].next_by_code("hyddemo.whs.liste"), 0

    def _create_whs_list_raw_move(
        self, move, num_lista, riga, is_custom, qty_producing=0
    ):
        whsliste_obj = self.env["hyddemo.whs.liste"]
        if not qty_producing and (
            move.whs_list_ids and not all(x.stato == "3" for x in move.whs_list_ids)
        ):
            return num_lista, riga
        if move.scrapped:
            return num_lista, riga
        if move.state in ("done", "cancel") and move.whs_list_ids:
            return num_lista, riga
        if move.product_uom_qty <= 0:
            return num_lista, riga
        if (
            move.product_id.type == "product"
            and not move.product_id.exclude_from_whs
            and move.location_id == self.location_src_id
        ):
            if not num_lista:
                num_lista, riga = self._get_num_lista()
            riga += 1
            if not qty_producing:
                qty_producing = move.product_uom_qty
            whsliste_data = dict(
                num_lista=num_lista,
                riga=riga,
                stato="1",
                data_lista=fields.Datetime.now(),
                riferimento=self.name,
                tipo=self._get_tipo(is_custom=is_custom),
                product_id=move.product_id.id,
                parent_product_id=self.product_id.id,
                qta=qty_producing,
                qtamov=qty_producing or move.quantity_done,
                move_id=move._origin.id,
                tipo_mov="mrpout",
            )
            whsliste_obj.create(whsliste_data)
            whsliste_obj.flush()
        return num_lista, riga

    def _create_whs_list_finished_move(self, move, num_lista, riga):
        whsliste_obj = self.env["hyddemo.whs.liste"]
        if move.whs_list_ids and not all(x.stato == "3" for x in move.whs_list_ids):
            return num_lista, riga
        if move.scrapped or (move.product_id.id != self.product_id.id):
            return num_lista, riga
        if move.state in ("done", "cancel") and move.whs_list_ids:
            return num_lista, riga
        if move.product_uom_qty <= 0:
            return num_lista, riga
        if move.location_dest_id == self.location_dest_id:
            if move.custom_check_mrp():
                return num_lista, riga
            if not num_lista:
                num_lista = self.env["ir.sequence"].next_by_code("hyddemo.whs.liste")
                riga = 0
            riga += 1
            whsliste_data = dict(
                stato="1",
                tipo="2",
                num_lista=num_lista,
                data_lista=fields.Datetime.now(),
                riferimento=self.name,
                product_id=move.product_id.id,
                qta=move.product_uom_qty,  # todo check correcteness
                qtamov=self.qty_producing,  # todo check correcteness
                move_id=move._origin.id,
                tipo_mov="mrpin",
                riga=riga,
            )
            whsliste_obj.create(whsliste_data)
        return num_lista, riga

    def _generate_whs(self):
        for production in self:
            # Create WMS lists for raw materials
            raw_dbsource = self.env["base.external.dbsource"].search(
                [
                    ("location_id", "=", production.location_src_id.id),
                    ("company_id", "=", production.company_id.id),
                ]
            )
            is_custom = (
                production.picking_type_id.warehouse_id.mto_pull_id.route_id
                in production.product_id.route_ids
                and production.product_id.categ_id.name == "CUSTOM"
            )
            if (
                raw_dbsource
                and len(raw_dbsource) == 1
                # and production.picking_type_id in raw_dbsource.stock_picking_type_ids
                # bypass check on locations, as this button is called from the user to
                # create directly whs lists
            ):
                num_lista = False
                riga = 0
                # Location of raw material is linked to WMS
                for move in production.move_raw_ids:
                    num_lista, riga = production._create_whs_list_raw_move(
                        move, num_lista, riga, is_custom
                    )

            # Create WMS list for finished products
            finished_dbsource = self.env["base.external.dbsource"].search(
                [
                    ("location_id", "=", production.location_dest_id.id),
                    ("company_id", "=", production.company_id.id),
                ]
            )
            if (
                finished_dbsource
                # and production.picking_type_id
                # in finished_dbsource.stock_picking_type_ids
                # bypass check on locations, as this button is called from the user to
                # create directly whs lists
                and not is_custom
            ):
                # Location of finished material is linked to WMS
                num_lista = False
                riga = 0
                for move in production.move_finished_ids:
                    num_lista, riga = production._create_whs_list_finished_move(
                        move, num_lista, riga)
