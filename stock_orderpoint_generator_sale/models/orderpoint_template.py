# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from odoo.tools.date_utils import relativedelta
from odoo import api, fields, models
from scipy.stats import norm
import math


class Orderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    orderpoint_tmpl_id = fields.Many2one(
        'stock.warehouse.orderpoint.template'
    )


class OrderpointTemplate(models.Model):
    _inherit = 'stock.warehouse.orderpoint.template'

    compute_on_sale = fields.Boolean()
    move_days = fields.Integer()
    service_level = fields.Float()
    order_mngt_cost = fields.Float()
    variation_percent = fields.Float(
        help="Increment/decrement value of qty by this percent")
    auto_min_date_start = fields.Datetime(
        compute='_compute_auto_date',
        help="This date is auto-computed every time this template is used.")
    auto_min_date_end = fields.Datetime(
        compute='_compute_auto_date',
        help="This date is auto-computed every time this template is used.")
    auto_max_date_start = fields.Datetime(
        compute='_compute_auto_date',
        help="This date is auto-computed every time this template is used.")
    auto_max_date_end = fields.Datetime(
        compute='_compute_auto_date',
        help="This date is auto-computed every time this template is used.")
    auto_max_qty_criteria = fields.Selection(
        selection_add=[('sum', 'Sum')])

    def _check_compute_on_sale(self):
        for rule in self:
            if rule.compute_on_sale:
                if rule.auto_max_qty_criteria != 'sum':
                    return False
        return True

    _constraints = [
        (_check_compute_on_sale,
         'You have to select "sum" as auto max qty criteria when "compute on sale" '
         'is selected',
         ['compute_on_sale', 'auto_max_qty_criteria']),
    ]

    @api.multi
    def _compute_auto_date(self):
        for op_template in self:
            date_start = datetime.now() + relativedelta(days=-op_template.move_days)
            date_end = datetime.now()
            op_template.auto_min_date_end = date_end
            op_template.auto_max_date_end = date_end
            op_template.auto_min_date_start = date_start
            op_template.auto_max_date_start = date_start

    @api.model
    def _get_criteria_methods(self):
        res = super()._get_criteria_methods()
        res.update({
            'sum': sum,
        })
        return res

    def _template_fields_to_discard(self):
        """In order to create every orderpoint we should pop this template
           customization fields """
        res = super()._template_fields_to_discard()
        for removed_field in ['auto_min_date_start', 'auto_min_date_end',
                              'auto_max_date_start', 'auto_max_date_end']:
            res.remove(removed_field)
        res += ['move_days', 'service_level', 'order_mngt_cost']
        return res

    def _create_instances(self, product_ids):
        """Create instances of model using template inherited model and
           compute autovalues if needed"""
        orderpoint_model = self.env['stock.warehouse.orderpoint']
        for record in self:
            # Flag equality so we compute the values just once
            auto_same_values = (
                record.auto_max_date_start == record.auto_min_date_start
                ) and (
                    record.auto_max_date_end == record.auto_max_date_end
                    ) and (
                        record.auto_max_qty_criteria ==
                        record.auto_min_qty_criteria)
            stock_min_qty = stock_max_qty = {}
            if record.auto_min_qty:
                stock_min_qty = (
                    self._get_product_qty_by_criteria(
                        product_ids,
                        location_id=record.location_id,
                        from_date=record.auto_min_date_start,
                        to_date=record.auto_min_date_end,
                        criteria=record.auto_min_qty_criteria,
                    ))
                if auto_same_values:
                    stock_max_qty = stock_min_qty
            if record.auto_max_qty and not stock_max_qty:
                if record.compute_on_sale:
                    stock_max_qty = (
                        self._get_product_qty_by_criteria_sale(
                            product_ids,
                            location_id=record.location_id,
                            from_date=record.auto_max_date_start,
                            to_date=record.auto_max_date_end,
                            criteria=record.auto_max_qty_criteria,
                        ))
                else:
                    stock_max_qty = (
                        self._get_product_qty_by_criteria(
                            product_ids,
                            location_id=record.location_id,
                            from_date=record.auto_max_date_start,
                            to_date=record.auto_max_date_end,
                            criteria=record.auto_max_qty_criteria,
                        ))
            for data in record.copy_data():
                for discard_field in self._template_fields_to_discard():
                    data.pop(discard_field)
                for product_id in product_ids:
                    vals = data.copy()
                    vals['product_id'] = product_id.id
                    # function taken from calc file
                    qty_by_day = stock_max_qty[product_id.id] / record.move_days
                    consumed_qty_by_lead_time = (
                            qty_by_day * (1 + record.variation_percent / 100.0)
                        ) * product_id.purchase_delay
                    service_factor = norm.ppf(record.service_level/100.0)
                    lead_time_factor = product_id.purchase_delay ** (1/2)
                    security_stock = int(math.ceil(
                        qty_by_day *
                        service_factor *
                        lead_time_factor))
                    min_qty = int(math.ceil(
                        consumed_qty_by_lead_time + security_stock
                    ))
                    lot_to_reorder = int(math.ceil(
                        (
                            2 *
                            record.order_mngt_cost *
                            qty_by_day *
                            record.move_days / (
                                0.15 * product_id.standard_price
                            )
                        ) ** (1/2)
                    ))
                    max_qty = min_qty + lot_to_reorder
                    # end function
                    if record.auto_min_qty:
                        vals['product_min_qty'] = min_qty
                    if record.auto_max_qty:
                        vals['product_max_qty'] = max_qty
                    vals['lead_days'] = product_id.purchase_delay
                    vals['qty_multiple'] = product_id.purchase_multiple_qty
                    vals['orderpoint_tmpl_id'] = record.id
                    orderpoint_model.create(vals)

    @api.model
    def _get_product_qty_by_criteria_sale(
            self, products, location_id, from_date, to_date, criteria):
        """Returns a dict with product ids as keys and the resulting
           calculation of historic moves according to criteria"""
        stock_qty_history = products._compute_historic_sale_quantities_dict(
            location_id=location_id,
            from_date=from_date,
            to_date=to_date)
        criteria_methods = self._get_criteria_methods()
        if criteria == 'sum':
            return {x: criteria_methods[criteria](y['move_history'])
                    for x, y in stock_qty_history.items()}
        return {x: criteria_methods[criteria](y['stock_history'])
                for x, y in stock_qty_history.items()}
