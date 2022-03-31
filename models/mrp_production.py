# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from datetime import timedelta


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

    @api.multi
    def record_production(self):
        if not self:
            return True
        self.ensure_one()
        res = super().record_production()
        if res:
            duration = self.production_id.mrp_end_produce(
                self.workcenter_id
            )
            if duration:
                timesheet = self.time_ids[0]
                timesheet.date_end = timesheet.date_start + timedelta(
                    minutes=duration)
        return res


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    bag_count_initial = fields.Integer(copy=False)
    bag_count_final = fields.Integer(copy=False)
    bag_count = fields.Integer(compute='_compute_bag_count', store=True)
    weight_initial = fields.Float(copy=False)
    weight_final = fields.Float(copy=False)
    weight = fields.Float(compute='_compute_weight', store=True)

    @api.multi
    @api.depends('bag_count_initial', 'bag_count_final')
    def _compute_bag_count(self):
        for mrp in self:
            mrp.bag_count = mrp.bag_count_final - mrp.bag_count_initial

    @api.multi
    @api.depends('weight_initial', 'weight_final')
    def _compute_weight(self):
        for mrp in self:
            mrp.weight = mrp.weight_final - mrp.weight_initial

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
    def mrp_end_produce(self, workcenter_id):
        # this function can be called many times, so we set initial fields only once
        # get info from iot.input.data for device linked to this workcenter
        for production in self:
            values = dict()
            duration = 0
            for key in ['weight', 'bag', 'duration']:
                iot_input_data_ids = self.env['iot.input.data'].search([
                    ('iot_device_input_id', '=', workcenter_id.iot_device_input_id.id),
                    ('timestamp', '<', fields.Datetime.now()),
                    ('name', 'ilike', key)
                ], order='timestamp DESC', limit=1)
                for iot_input_data in iot_input_data_ids:
                    if key == 'weight' and not production.weight_final:
                        values.update(weight_final=iot_input_data.value)
                    if key == 'bag' and not production.bag_count_final:
                        values.update(bag_count_final=iot_input_data.value)
                    if key == 'duration':
                        duration = int(iot_input_data.value)
            if values:
                production.write(values)
            return duration

        #todo in una funzione successiva?
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
