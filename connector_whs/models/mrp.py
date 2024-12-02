# Copyright 2013 Maryam Noorbakhsh creativiquadrati snc
# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.multi
    def button_mark_done(self):
        res = super().button_mark_done()
        self._generate_whs()
        return res

    @api.multi
    def post_inventory(self):
        if any(
                x.stato != '4' and x.qta
                for x in self.move_raw_ids.mapped('whs_list_ids')):
            raise UserError(_('Almost a WHS list is not in state "Ricevuto Esito"!'))
        res = super().post_inventory()
        return res

    @api.multi
    def _get_whslist_component_data(self, num_lista, riga, move):
        # overridable method
        return dict(
            data_lista=fields.Datetime.now(),
            move_id=move.id,
            num_lista=num_lista,
            parent_product_id=self.product_id.id,
            product_id=move.product_id.id,
            qta=move.quantity_done,
            riferimento=self.name,
            riga=riga,
            stato='1',
            tipo='1',
            tipo_mov='mrpout',
        )

    @api.multi
    def _get_whslist_finished_data(self, num_lista, riga, move):
        # overridable method
        return dict(
            data_lista = fields.Datetime.now(),
            move_id = move.id,
            num_lista = num_lista,
            product_id = move.product_id.id,
            qta = move.quantity_done,
            riferimento = self.name,
            riga = riga,
            stato = '1',
            tipo = '2',
            tipo_mov = 'mrpin',
        )

    @api.multi
    def _generate_whs(self):
        # FIXME: this works only for complete production, add support for partial
        #  production
        whsliste_obj = self.env['hyddemo.whs.liste']
        for production in self:
            # Create WHS list for raw materials
            raw_dbsource = self.env['base.external.dbsource'].search([
                ('location_id', '=', production.location_src_id.id)
            ])
            if raw_dbsource:
                num_lista = False
                # Location of raw material is linked to WHS
                for move in production.move_raw_ids:
                    if move.scrapped:
                        continue
                    if move.state in ('done', 'cancel') and move.whs_list_ids:
                        continue
                    if move.quantity_done <= 0:
                        continue
                    if (
                        move.product_id.type == "product"
                        and not move.product_id.exclude_from_whs
                        and move.location_id == production.location_src_id
                    ):
                        if not num_lista:
                            num_lista = self.env['ir.sequence'].next_by_code(
                                'hyddemo.whs.liste')
                            riga = 0
                        riga += 1
                        whsliste_data = production._get_whslist_component_data(
                            num_lista, riga, move
                        )
                        whsliste_obj.create(whsliste_data)

            # Create WHS list for finished products
            finished_dbsource = self.env['base.external.dbsource'].search([
                ('location_id', '=', production.location_dest_id.id)
            ])
            if finished_dbsource:
                # Location of finished material is linked to WHS
                num_lista = False
                for move in production.move_finished_ids:
                    if move.scrapped or (
                            move.product_id.id != production.product_id.id):
                        continue
                    if move.state in ('done', 'cancel') and move.whs_list_ids:
                        continue
                    if move.quantity_done <= 0:
                        continue
                    if move.location_dest_id == production.location_dest_id:
                        if all([x in [
                            self.env.ref('mrp.route_warehouse0_manufacture'),
                            self.env.ref('stock.route_warehouse0_mto')
                        ]
                                for x in move.product_id.route_ids]):
                            # Never create whs list for OUT or IN related to
                            # manufactured products, only create MO.
                            # The IN will be without whs_list_ids so freely validatable
                            # as production is done.
                            # Same for the OUT, that one will be based only on Odoo
                            # stock current availability (user has to check this one is
                            # correct)
                            if move.procure_method == 'make_to_order':
                                continue
                        if not num_lista:
                            num_lista = self.env['ir.sequence'].next_by_code(
                                'hyddemo.whs.liste')
                            riga = 0
                        riga += 1
                        whsliste_data = production._get_whslist_finished_data(
                            num_lista, riga, move
                        )
                        whsliste_obj.create(whsliste_data)


class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"

    @api.multi
    def do_produce(self):
        res = super().do_produce()
        production_id = self._context.get('active_id', False)
        production = self.env['mrp.production'].browse([production_id])
        production._generate_whs()
        return res
