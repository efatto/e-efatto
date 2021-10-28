# Copyright 2013 Maryam Noorbakhsh creativiquadrati snc
# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _


class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"

    @api.multi
    def do_produce(self):
        res = super(MrpProductProduce, self).do_produce()
        # FIXME: this works only for complete production, add support for partial
        #  production
        production_id = self._context.get('active_id', False)
        mo_obj = self.env['mrp.production']
        whsliste_obj = self.env['hyddemo.whs.liste']
        for production in mo_obj.browse([production_id]):
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
                    if move.state in ('done', 'cancel'):
                        continue
                    if move.quantity_done <= 0:
                        continue
                    if move.product_id.type == 'product' \
                            and move.location_id == production.location_src_id:
                        if not num_lista:
                            num_lista = self.env['ir.sequence'].next_by_code(
                                'hyddemo.whs.liste')
                            riga = 0
                        riga += 1
                        whsliste_data = dict(
                            num_lista=num_lista,
                            riga=riga,
                            stato='1',
                            data_lista=fields.Datetime.now(),
                            riferimento=production.name,
                            tipo='1',
                            product_id=move.product_id.id,
                            parent_product_id=production.product_id.id,
                            qta=move.quantity_done,
                            move_id=move.id,
                            tipo_mov='mrpout',
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
                    if move.scrapped or (move.product_id.id != production.product_id.id):
                        continue
                    if move.state in ('done', 'cancel'):
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
                        whsliste_data = dict(
                            stato='1',
                            tipo='2',
                            num_lista=num_lista,
                            data_lista=fields.Datetime.now(),
                            riferimento=production.name,
                            product_id=move.product_id.id,
                            qta=move.quantity_done,
                            move_id=move.id,
                            tipo_mov='mrpin',
                            riga=riga,
                        )
                        whsliste_obj.create(whsliste_data)
        return res
