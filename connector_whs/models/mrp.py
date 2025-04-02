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

    # state = fields.Selection(
    #     selection_add=[("consumed", "Consumed"), ("done", "Done")],
    #     help=" * Confirmed: The MO is confirmed, the stock rules and the reordering of "
    #     "the components are trigerred.\n"
    #     " * Planned: The production is planned.\n"
    #     " * In Progress: The production has started (on the MO or on the WO).\n"
    #     " * Consumed: The production is in progress, raw components has been "
    #     "moved from stock to production area.\n"
    #     " * Done: The MO is closed, the stock moves are posted. \n"
    #     " * Cancelled: The MO has been cancelled, can't be confirmed anymore.",
    # )
    moves_to_do_ids = fields.Many2many(
        comodel_name="stock.move",
        string="Technical field to store moves to do in consume workflow",
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

    # def button_consume(self):
    #     # self._button_mark_done_sanity_checks()
    #     for production in self:
    #         if (
    #             # production.bom_id.type != "subcontract" and
    #             not production.sent_to_wms
    #             and production.state
    #             not in [
    #                 "done",
    #                 "cancel",
    #             ]
    #         ):
    #             raise UserError(
    #                 _("Production %s has not been sent to WMS!") % production.name
    #             )
    #         production.move_raw_ids._check_done_whs_list()
    #         if production.state == "progress":
    #             moves_to_do = production.move_raw_ids.filtered(
    #                 lambda x: x.state not in ("done", "cancel")
    #             )
    #             for move in moves_to_do.filtered(
    #                 lambda m: m.product_qty == 0.0 and m.quantity_done > 0
    #             ):
    #                 move.product_uom_qty = move.quantity_done
    #             # MRP do not merge move, catch the result of _action_done in order
    #             # to get extra moves.
    #             moves_to_do = moves_to_do._action_done()
    #             production._cal_price(moves_to_do)
    #             production.action_assign()
    #             production.moves_to_do_ids = [(6, 0, moves_to_do.ids)]

    # @api.multi
    # def button_mark_done(self):
    #     for production in self:
    #         # check bom type only to exclude subcontract if installed, without adding
    #         # a dependency
    #         # if (
    #         #     not config["test_enable"] or self.env.context.get("test_connector_whs")
    #         # ) and (
    #         #     # not production.sent_to_wms
    #         #     # and
    #         #     production.bom_id.type in ["normal", "phantom"]
    #         #     and production.state
    #         #     not in [
    #         #         "done",
    #         #         "cancel",
    #         #     ]
    #         # ):
    #         #     raise UserError(
    #         #         _("Production %s has not been sent to WMS!") % production.name
    #         #     )
    #         (
    #             production.move_raw_ids | production.move_finished_ids
    #         )._check_done_whs_list()
    #         if production.state == "consumed":
    #             production.write({"state": "progress"})
    #     res = super().button_mark_done()
    #     for production in self:
    #         if not production.move_finished_ids.move_line_ids.consume_line_ids:
    #             production.move_finished_ids.move_line_ids.consume_line_ids = [
    #                 (6, 0, production.moves_to_do_ids.mapped("move_line_ids").ids)
    #             ]
    #             production.moves_to_do_ids = [(5,)]
    #     return res

    # def button_send_to_wms(self):
    #     self._generate_wms()
    #     self._compute_sent_to_wms()

    @api.multi
    def post_inventory(self):
        (self.move_raw_ids | self.move_finished_ids)._check_done_whs_list()
        # todo check
        if any(
                x.stato != "4" and x.qta
                for x in self.move_raw_ids.mapped("whs_list_ids")):
            raise UserError(_("Almost a WMS list is not in state 'Ricevuto Esito'!"))
        # end check
        res = super().post_inventory()
        return res

    # @api.multi
    # def _get_whslist_component_data(self, num_lista, riga, move):
    #     # overridable method
    #     return dict(
    #         data_lista=fields.Datetime.now(),
    #         move_id=move.id,
    #         num_lista=num_lista,
    #         parent_product_id=self.product_id.id,
    #         product_id=move.product_id.id,
    #         qta=move.quantity_done,
    #         riferimento=self.name,
    #         riga=riga,
    #         stato="1",
    #         tipo="1",
    #         tipo_mov="mrpout",
    #     )
    #
    # @api.multi
    # def _get_whslist_finished_data(self, num_lista, riga, move):
    #     # overridable method
    #     return dict(
    #         data_lista=fields.Datetime.now(),
    #         move_id=move.id,
    #         num_lista=num_lista,
    #         product_id=move.product_id.id,
    #         qta=move.quantity_done,
    #         riferimento=self.name,
    #         riga=riga,
    #         stato="1",
    #         tipo="2",
    #         tipo_mov="mrpin",
    #     )

    @api.multi
    def _generate_wms(self):
        whsliste_obj = self.env["hyddemo.whs.liste"]
        for production in self:
            # Create WMS list for raw materials
            raw_dbsource = self.env["base.external.dbsource"].search([
                ("location_id", "=", production.location_src_id.id),
                ("company_id", "=", production.company_id.id),
            ])
            if (
                raw_dbsource and production.picking_type_id
                in raw_dbsource.stock_picking_type_ids
            ):
                num_lista = False
                riga = 0
                # Location of raw material is linked to WMS
                for move in production.move_raw_ids:
                    if move.whs_list_ids and not all(
                        x.stato == "3" for x in move.whs_list_ids
                    ):
                        continue
                    if move.scrapped:
                        continue
                    if move.state in ("done", "cancel") and move.whs_list_ids:
                        continue
                    if move.quantity_done <= 0:
                        continue
                    if (
                        move.product_id.type == "product"
                        and not move.product_id.exclude_from_whs
                        and move.location_id == production.location_src_id
                    ):
                        if not num_lista:
                            num_lista = self.env["ir.sequence"].next_by_code(
                                "hyddemo.whs.liste")
                            riga = 0
                        riga += 1
                        whsliste_data = dict(
                            num_lista=num_lista,
                            riga=riga,
                            stato="1",
                            data_lista=fields.Datetime.now(),
                            riferimento=production.name,
                            tipo="1",
                            product_id=move.product_id.id,
                            parent_product_id=production.product_id.id,
                            qta=move.quantity_done,
                            move_id=move.id,
                            tipo_mov="mrpout",
                        )
                        whsliste_obj.create(whsliste_data)

            # Create WMS list for finished products
            finished_dbsource = self.env["base.external.dbsource"].search([
                ("location_id", "=", production.location_dest_id.id),
                ("company_id", "=", production.company_id.id),
            ])
            if (
                finished_dbsource
                and production.picking_type_id
                in finished_dbsource.stock_picking_type_ids
            ):
                # Location of finished material is linked to WMS
                num_lista = False
                riga = 0
                for move in production.move_finished_ids:
                    if move.whs_list_ids and not all(
                        x.stato == "3" for x in move.whs_list_ids
                    ):
                        continue
                    if move.scrapped or (
                            move.product_id.id != production.product_id.id):
                        continue
                    if move.state in ("done", "cancel") and move.whs_list_ids:
                        continue
                    if move.quantity_done <= 0:
                        continue
                    if move.location_dest_id == production.location_dest_id:
                        if all([x in [
                            self.env.ref("mrp.route_warehouse0_manufacture"),
                            self.env.ref("stock.route_warehouse0_mto")
                        ]
                                for x in move.product_id.route_ids]):
                            # Never create wms list for OUT or IN related to
                            # manufactured products, only create MO.
                            # The IN will be without whs_list_ids so freely validatable
                            # as production is done.
                            # Same for the OUT, that one will be based only on Odoo
                            # stock current availability (user has to check this one is
                            # correct)
                            if move.procure_method == "make_to_order":
                                continue
                        if not num_lista:
                            num_lista = self.env["ir.sequence"].next_by_code(
                                "hyddemo.whs.liste")
                            riga = 0
                        riga += 1
                        whsliste_data = dict(
                            stato="1",
                            tipo="2",
                            num_lista=num_lista,
                            data_lista=fields.Datetime.now(),
                            riferimento=production.name,
                            product_id=move.product_id.id,
                            qta=production.qty_produced,
                            move_id=move.id,
                            tipo_mov="mrpin",
                            riga=riga,
                        )
                        whsliste_obj.create(whsliste_data)


class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"

    @api.multi
    def do_produce(self):
        res = super().do_produce()
        production_id = self._context.get("active_id", False)
        production = self.env["mrp.production"].browse([production_id])
        production._generate_wms()
        return res
