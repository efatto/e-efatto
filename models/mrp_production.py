# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    @api.multi
    def button_start(self):
        self.ensure_one()
        res = super().button_start()
        if res:
            self.production_id.mrp_start_produce(
                self.workcenter_id
            )
        return res


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    bag_count_initial = fields.Integer()
    bag_count_final = fields.Integer()
    bagging_duration = fields.Float()
    weight_initial = fields.Float()
    weight_final = fields.Float()

    @api.multi
    def mrp_start_produce(self, workcenter_id):
        # this function can be called many times, so we set initial fields only once
        # get info from iot.input.data for device linked to this workcenter
        for production in self:
            values = dict()
            for key in ['weight', 'bag']:
                iot_input_data_ids = self.env['iot.input.data'].search([
                    ('iot_device_input_id', '=', workcenter_id.iot_device_input_id.id),
                    ('timestamp', '<', fields.Datetime.now()),
                    ('name', 'ilike', key)
                ], order='timestamp DESC', limit=1)
                for iot_input_data in iot_input_data_ids:
                    if key == 'weight' and not production.weight_initial:
                        values.update(weight_initial=iot_input_data.value)
                    if key == 'bag' and not production.bag_count_initial:
                        values.update(bag_count_initial=iot_input_data.value)
            if values:
                production.write(values)

    @api.multi
    def mrp_end_produce(self):
        #todo
        # set moves weight proportionally to weight received
        # weight_uom_cat_id = self.env['uom.category'].search([
        #     ('measure_type', '=', 'weight')
        # ])[0]
        # reference_weight_uom_id = self.env['uom.uom'].search([
        #     ('category_id', '=', weight_uom_cat_id.id),
        #     ('uom_type', '=', 'reference'),
        # ])
        # moves = production.move_raw_ids.filtered(
        #     lambda x: x.product_uom.category_id == weight_uom_cat_id
        # )
        # # sum all weights converted to reference uom weight
        # total_weight = sum(
        #     x.product_uom._compute_quantity(
        #         x.product_uom_qty,
        #         reference_weight_uom_id,
        #         round=False)
        #     for x in moves
        # )
        # if total_weight:
        #     coef = production_weight / total_weight
        #     for move in moves:
        #         move.product_uom_qty = move.product_uom_qty * coef
        #     res = True
        #todo creare in automatico il product_lot?
        # lot_id = self.env['stock.production.lot'].create([{
        #     'product_id': production.product_id.id,
        #     'name': 'new lot name?',
        # }])
        # if lot_id:
        #     values.update(
        #         dict(lot_id=lot_id.id)
        #     )
        #todo produrre solo alla fine? questa funzione viene chiamata solo alla fine
        # quando c'è il routing
        # produce = self.env['mrp.product.produce'].with_context(
        #     default_production_id=production.id,
        #     active_id=production.id).create(values)
        # produce._onchange_product_qty()
        # res = produce.do_produce()
        pass
