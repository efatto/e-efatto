# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    bom_line_id = fields.Many2one(
        comodel_name='mrp.bom.line',
    )
    estimated_purchase_price = fields.Float(
        string='Estimated Cost',
        digits=dp.get_precision('Product Price'),
    )
    final_purchase_price = fields.Float(
        string='Final Cost',
        help='Direct costs plus a proportion of analytic costs',
        digits=dp.get_precision('Product Price'),
    )
    lead_line_id = fields.Many2one(
        comodel_name='crm.lead.line',
        compute="_compute_lead_line_id",
        store=True,
        index=True,
    )
    mrp_production_ids = fields.Many2many(
        comodel_name='mrp.production',
        compute='_compute_mrp_production_ids',
        compute_sudo=True,
        store=True,
        index=True,
    )
    mrp_production_total_amount = fields.Float(
        compute='_compute_mrp_production_total_amount',
        store=True,
    )
    workorder_price_subtotal = fields.Float(
        string='Workorder Price Subtotal',
        compute='_compute_mrp_production_total_amount',
        store=True,
    )
    move_raw_price_subtotal = fields.Float(
        string='MRP Move Price Subtotal',
        compute='_compute_mrp_production_total_amount',
        store=True,
    )

    @api.depends(
        'mrp_production_ids.total_amount',
        'mrp_production_ids.workorder_price_subtotal',
        'mrp_production_ids.move_raw_price_subtotal',
    )
    def _compute_mrp_production_total_amount(self):
        for line in self:
            line.mrp_production_total_amount = sum(
                mrp.total_amount for mrp in line.mrp_production_ids)
            line.workorder_price_subtotal = sum(
                mrp.workorder_price_subtotal for mrp in line.mrp_production_ids)
            line.move_raw_price_subtotal = sum(
                mrp.move_raw_price_subtotal for mrp in line.mrp_production_ids)

    @api.depends("order_id.opportunity_id")
    def _compute_lead_line_id(self):
        for line in self:
            lead_line_id = self.env["crm.lead.line"].browse()
            lead_line_ids = line.order_id.opportunity_id.lead_line_ids
            if lead_line_ids:
                lead_line_id = line.order_id.opportunity_id.lead_line_ids.filtered(
                    lambda x: x.product_id == line.product_id
                )[:1]
            line.lead_line_id = lead_line_id

    @api.depends("lead_line_id", "product_id")
    def _compute_mrp_production_ids(self):
        for line in self:
            if line.lead_line_id:
                mrp_production_ids = self.env['mrp.production'].search([
                    ("lead_line_id", "=", line.lead_line_id.id),
                    ("state", "!=", "cancel"),
                ])
            else:
                mrp_production_ids = self.env['mrp.production'].search([
                    ("sale_id", "=", line.order_id.id),
                    ("product_id", "=", line.product_id.id),
                    ("state", "!=", "cancel"),
                ])
            line.mrp_production_ids = mrp_production_ids


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_cancel(self):
        res = super().action_cancel()
        lines = self.order_line.sudo().filtered(lambda x: x.bom_line_id)
        lines.unlink()
        return res

    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        # do not duplicate lines auto-created
        self.ensure_one()
        default = dict(default or {})
        res = super().copy(default)
        lines = res.order_line.filtered(lambda x: x.bom_line_id)
        lines.unlink()
        return res

    @api.multi
    def write(self, values):
        res = super().write(values)
        # recalculate bom cost at every change of a sale order
        self.recalculate_bom_costs()
        return res

    @api.model
    def _cron_recalculate_bom_costs(self):
        # this cron ensure that bom costs are aligned when a bom is changed and the
        # sale orders with that product are not
        sale_orders = self.env["sale.order"].search([
            ('order_line.product_id.bom_ids', '!=', False),
        ])
        sale_order_to_recomputes = self.env["sale.order"].browse()
        for sale_order in sale_orders:
            # consider only the boms updated/created after the last write on sale order
            bom_to_recomputes = self.env["mrp.bom"].search([
                ("write_date", ">", sale_order.write_date),
                "|",
                ("product_id", "in", sale_order.mapped("order_line.product_id.id")),
                ("product_tmpl_id", "in", sale_order.mapped(
                    "order_line.product_id.product_tmpl_id.id")),
            ])
            if bom_to_recomputes:
                sale_order_to_recomputes |= sale_order
        _logger.info(
            "Start recalculate bom costs job for #%s sale orders." %
            len(sale_order_to_recomputes)
        )
        sale_order_to_recomputes.recalculate_bom_costs()
        _logger.info(
            "End recalculate bom costs job for #%s sale orders." %
            len(sale_order_to_recomputes)
        )

    @api.multi
    def recalculate_bom_costs(self):
        for order in self:
            lines = order.order_line.filtered(
                lambda x: x.product_id and x.product_id.bom_count > 0
            )
            lines.mapped('product_id').with_context(
                order_revision="ASC"
            ).action_bom_cost()
            for line in lines:
                line.estimated_purchase_price = line._compute_margin(
                    order, line.product_id, line.product_uom
                )
            lines.mapped('product_id').with_context(
                order_revision="DESC"
            ).action_bom_cost()
            for line in lines:
                line.purchase_price = line._compute_margin(
                    order, line.product_id, line.product_uom
                )
