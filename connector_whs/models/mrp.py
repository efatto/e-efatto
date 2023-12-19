# Copyright 2013 Maryam Noorbakhsh creativiquadrati snc
# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# flake8: noqa: C901
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    sent_to_whs = fields.Boolean(
        string="Sent to WHS",
        compute="_compute_sent_to_whs",
        store=True,
    )

    @api.depends("move_raw_ids.whs_list_ids", "move_finished_ids.whs_list_ids")
    def _compute_sent_to_whs(self):
        for production in self.filtered(lambda mo: mo.state not in ["done", "cancel"]):
            production.sent_to_whs = all(
                x.whs_list_ids
                and not all(whs_list.tipo == "3" for whs_list in x.whs_list_ids)
                for x in (
                    production.move_finished_ids | production.move_raw_ids
                ).filtered(lambda move: move.state != "done")
            )
        for production in self.filtered(lambda mo: mo.state in ["done", "cancel"]):
            production.sent_to_whs = False

    def button_mark_done(self):
        for production in self:
            if production.state != "progress":
                raise UserError(_("Production %s is not in progress.") % production)
        return super().button_mark_done()

    def button_send_to_whs(self):
        self._generate_whs()

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
        if any(
            x.stato != "4" and x.qta
            for x in (self.move_raw_ids | self.move_finished_ids).mapped("whs_list_ids")
        ):
            raise UserError(_('Almost a WHS list is not in state "Ricevuto Esito"!'))
        res = super()._post_inventory(cancel_backorder=cancel_backorder)
        return res

    def _generate_whs(self):
        whsliste_obj = self.env["hyddemo.whs.liste"]
        for production in self:
            # Create WHS list for raw materials
            raw_dbsource = self.env["base.external.dbsource"].search(
                [("location_id", "=", production.location_src_id.id)]
            )
            if raw_dbsource:
                num_lista = False
                riga = 0
                # Location of raw material is linked to WHS
                for move in production.move_raw_ids:
                    if move.whs_list_ids and not all(
                        x.stato == "3" for x in move.whs_list_ids
                    ):
                        continue
                    if move.scrapped:
                        continue
                    if move.state in ("done", "cancel") and move.whs_list_ids:
                        continue
                    if move.product_uom_qty <= 0:
                        continue
                    if (
                        move.product_id.type == "product"
                        and move.location_id == production.location_src_id
                    ):
                        if not num_lista:
                            num_lista = self.env["ir.sequence"].next_by_code(
                                "hyddemo.whs.liste"
                            )
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
                            move_id=move._origin.id,
                            tipo_mov="mrpout",
                        )
                        whsliste_obj.create(whsliste_data)

            # Create WHS list for finished products
            finished_dbsource = self.env["base.external.dbsource"].search(
                [("location_id", "=", production.location_dest_id.id)]
            )
            if finished_dbsource and not (
                production.picking_type_id.warehouse_id.mto_pull_id.route_id
                in production.product_id.route_ids
            ):
                # Do not create WHS lists for finished products that have an MTO route
                # Location of finished material is linked to WHS
                num_lista = False
                riga = 0
                for move in production.move_finished_ids:
                    if move.whs_list_ids and not all(
                        x.stato == "3" for x in move.whs_list_ids
                    ):
                        continue
                    if move.scrapped or (
                        move.product_id.id != production.product_id.id
                    ):
                        continue
                    if move.state in ("done", "cancel") and move.whs_list_ids:
                        continue
                    if move.product_uom_qty <= 0:
                        continue
                    if move.location_dest_id == production.location_dest_id:
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
                            # Never create whs list for OUT or IN related to
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
                                "hyddemo.whs.liste"
                            )
                            riga = 0
                        riga += 1
                        whsliste_data = dict(
                            stato="1",
                            tipo="2",
                            num_lista=num_lista,
                            data_lista=fields.Datetime.now(),
                            riferimento=production.name,
                            product_id=move.product_id.id,
                            qta=production.qty_producing,
                            move_id=move._origin.id,
                            tipo_mov="mrpin",
                            riga=riga,
                        )
                        whsliste_obj.create(whsliste_data)
