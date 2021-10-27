# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    @api.multi
    def action_repair_end(self):
        res = super(RepairOrder, self).action_repair_end()
        whsliste_obj = self.env['hyddemo.whs.liste']
        for repair in self:
            location_id = repair.location_id
            dbsource = self.env['base.external.dbsource'].search([
                ('location_id', '=', location_id.id)
            ])
            if not dbsource:
                # This location is not linked to WHS System
                continue
            add_operations = repair.operations.filtered(
                lambda x: x.move_id and x.move_id.state == 'done'
                and x.move_id.product_id.type == 'product'
                and x.move_id.location_id == location_id)
            remove_operations = repair.operations.filtered(
                lambda x: x.move_id and x.move_id.state == 'done'
                          and x.move_id.product_id.type == 'product'
                          and x.move_id.location_dest_id == location_id)
            if add_operations:
                num_lista = self.env['ir.sequence'].next_by_code('hyddemo.whs.liste')
                for riga, op in enumerate(add_operations, start=1):
                    move = op.move_id
                    whsliste_data = dict(
                        stato='1',
                        tipo='1',
                        num_lista=num_lista,
                        data_lista=fields.Datetime.now(),
                        riferimento=repair.name,
                        product_id=move.product_id.id,
                        qta=move.product_uom_qty,
                        move_id=move.id,
                        tipo_mov='ripout',
                        riga=riga,
                    )
                    whsliste_obj.create(whsliste_data)
            if remove_operations:
                num_lista = self.env['ir.sequence'].next_by_code('hyddemo.whs.liste')
                for riga, op in enumerate(remove_operations, start=1):
                    move = op.move_id
                    whsliste_data = dict(
                        stato='1',
                        num_lista=num_lista,
                        data_lista=fields.Datetime.now(),
                        tipo='2',
                        riferimento=repair.name,
                        product_id=move.product_id.id,
                        qta=move.product_uom_qty,
                        move_id=move.id,
                        tipo_mov='ripin',
                        riga=riga,
                    )
                    whsliste_obj.create(whsliste_data)

        return res
