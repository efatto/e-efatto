# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    lead_line_id = fields.Many2one(
        comodel_name='crm.lead.line',
        index=True,
    )
    workorder_price_subtotal = fields.Float(
        compute='_compute_workorder_price_subtotal',
        compute_sudo=True,
        store=True,
        groups='account.group_account_user',
    )
    move_raw_price_subtotal = fields.Float(
        compute='_compute_move_raw_price_subtotal',
        compute_sudo=True,
        store=True,
        groups='account.group_account_user',
    )
    total_amount = fields.Float(
        compute='_compute_total_amount',
        compute_sudo=True,
        store=True)

    @api.multi
    @api.depends(
        'workorder_price_subtotal',
        'move_raw_price_subtotal')
    def _compute_total_amount(self):
        for production in self:
            production.total_amount = (
                production.workorder_price_subtotal
                + production.move_raw_price_subtotal
            )

    @api.depends(
        'workorder_ids.time_ids.duration',
        'workorder_ids.time_ids.loss_type',
        'workorder_ids.time_ids.workcenter_id.costs_hour',
    )
    def _compute_workorder_price_subtotal(self):
        for production in self:
            production.workorder_price_subtotal = sum(
                time.workcenter_id.costs_hour / 60.0 *
                time.duration
                for time in
                production.mapped("workorder_ids.time_ids").filtered(
                    lambda x: x.loss_type == 'productive'
                )
            )

    @api.depends('move_raw_ids.price_unit', 'move_raw_ids.quantity_done')
    def _compute_move_raw_price_subtotal(self):
        for production in self:
            if any(x.price_unit > 0 for x in production.move_raw_ids):
                _logger.info("Some positive stock move price unit in production %s"
                             % production.name)
            production.move_raw_price_subtotal = sum(
                abs(move.price_unit) * move.quantity_done
                for move in production.move_raw_ids
            )

    def _get_raw_move_data(self, bom_line, line_data):
        if bom_line.product_id.exclude_from_mo:
            return
        if bom_line.product_id.type == 'service' and self.sale_id and not any(
            x.bom_line_id == bom_line
            for x in self.sale_id.order_line
        ):
            # add SO order line to create task and/or project, excluding lines already
            # created with bom_line_id, with order project_id created from
            # sale_order_analytic_all
            vals = {
                'name': "%s - %s" % (
                    bom_line.product_id.name,
                    bom_line.bom_id.product_id.name
                ),
                'product_id': bom_line.product_id.id,
                'product_uom_qty': line_data['qty'],
                'product_uom': bom_line.product_id.uom_id.id,
                'price_unit': 0,
                'order_id': self.sale_id.id,
                'bom_line_id': bom_line.id,
                'project_id': self.sale_id.project_id.id,
            }
            if self.sale_id.order_line:
                line = self.sale_id.order_line.filtered(
                    lambda x: x.product_id == bom_line.bom_id.product_id
                )
                if line:
                    sequence = line[0].sequence
                    vals.update(sequence=sequence)
            self.env['sale.order.line'].create(vals)
            return
        return super()._get_raw_move_data(bom_line, line_data)
