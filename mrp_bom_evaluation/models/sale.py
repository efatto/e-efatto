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
        string='Cost in Sale Offer',
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
        compute_sudo=True,
        store=True,
    )
    workorder_price_subtotal = fields.Float(
        string='Workorder Price Subtotal',
        compute='_compute_mrp_production_total_amount',
        compute_sudo=True,
        store=True,
    )
    move_raw_price_subtotal = fields.Float(
        string='MRP Move Price Subtotal',
        compute='_compute_mrp_production_total_amount',
        compute_sudo=True,
        store=True,
    )
    analytic_cost = fields.Float(
        string='Analytic Cost',
        compute='_compute_mrp_production_total_amount',
        compute_sudo=True,
        store=True,
    )
    total_cost = fields.Float(
        string='Total Cost',
        compute='_compute_mrp_production_total_amount',
        compute_sudo=True,
        store=True,
    )
    final_purchase_price = fields.Float(
        string='Total Cost Unit',
        compute='_compute_mrp_production_total_amount',
        compute_sudo=True,
        store=True,
        help='Direct costs plus a proportion of analytic costs',
        digits=dp.get_precision('Product Price'),
    )

    def _compute_mrp_production_total_amount(self):
        for line in self:
            line.analytic_cost = (
                line.order_id.extra_cost
                + line.order_id.internal_timesheet_cost
            ) * line.price_subtotal / (line.order_id.amount_untaxed or 1.0)
            line.mrp_production_total_amount = sum(
                mrp.total_amount for mrp in line.mrp_production_ids)
            line.workorder_price_subtotal = sum(
                mrp.workorder_price_subtotal for mrp in line.mrp_production_ids)
            line.move_raw_price_subtotal = sum(
                mrp.move_raw_price_subtotal for mrp in line.mrp_production_ids)
            line.total_cost = (
                line.analytic_cost + line.move_raw_price_subtotal
                + line.workorder_price_subtotal)
            line.final_purchase_price = line.total_cost / (line.qty_delivered or 1.0)

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

    extra_cost = fields.Float(
        string="Analytic Actual Cost",
        compute="_compute_analytic_cost",
        store=True,
    )
    internal_timesheet_cost = fields.Float(
        string="Analytic Internal Timesheet Cost",
        compute="_compute_analytic_cost",
        store=True,
    )

    def _compute_analytic_cost(self):
        for sale in self:
            extra_costs = self.env["account.analytic.line"].search([
                ('project_id', '=', False),
                ('account_id', '=', sale.analytic_account_id.id),
                ('move_id.invoice_id.type', 'in', ['in_invoice', 'in_refund'])
            ])
            internal_timesheet_costs = self.env['account.analytic.line'].search([
                ('employee_id', '!=', False),
                ('account_id', '=', sale.analytic_account_id.id),
                ('project_id.name', '!=', 'Internal Project'),
                ('so_line.product_id.categ_id.id', '=', '27'),
            ])
            analytic_sale_lines = self.env['sale.order.line'].search([
                ('order_id.analytic_account_id', '=', sale.analytic_account_id.id),
            ])
            analytic_sale_revenue = sum(
                analytic_sale_lines.mapped('price_subtotal') or [0])
            sale.extra_cost = - sum(extra_costs.mapped('extra_cost') or [0]) * (
                sale.amount_untaxed / (analytic_sale_revenue or 1.0)
            )
            # sale.extra_cost_no_product = - sum(
            #     extra_costs.mapped('extra_cost_no_product') or [0]
            # ) * (
            #     sale.amount_untaxed / (analytic_sale_revenue or 1.0)
            # )
            sale.internal_timesheet_cost = - sum(
                internal_timesheet_costs.mapped('amount') or [0]) * (
                sale.amount_untaxed / (analytic_sale_revenue or 1.0)
            )

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
    def recalculate_all_costs(self):
        # Recalculate bom, mrp and analytic cost at every change of a sale order.
        # The same methods are called from the cron when modifications are done only
        # on the mrp, move or analytic objects.
        self.mapped('order_line')._compute_mrp_production_ids()
        self._recalculate_bom_costs()
        self.mapped('production_ids')._compute_workorder_price_subtotal()
        self.mapped('production_ids')._compute_move_raw_price_subtotal()
        self._compute_analytic_cost()
        self.mapped('order_line')._compute_mrp_production_total_amount()


    @api.model
    def _cron_recalculate_all_costs(self):
        # this cron ensures that all costs are aligned when a bom is changed and the
        # sale orders with that product are not
        sale_orders = self.env["sale.order"].search([
            ('order_line.product_id.bom_ids', '!=', False),
        ])
        _logger.info(
            "Start recalculate all costs job for #%s sale orders." %
            len(sale_orders)
        )
        sale_orders._recalculate_bom_costs()
        _logger.info(
            "End recalculate all costs job for #%s sale orders." %
            len(sale_orders)
        )

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
        sale_order_to_recomputes._recalculate_bom_costs()
        _logger.info(
            "End recalculate bom costs job for #%s sale orders." %
            len(sale_order_to_recomputes)
        )
        # recalculate costs only for sale order with a production changed in something
        # after last write in sale order
        sale_mrp_order_to_recomputes = self.env["sale.order"].browse()
        for sale_order in sale_orders:
            mrp_to_recomputes = sale_order.production_ids.filtered(
                lambda mrp:
                mrp.write_date > sale_order.write_date
                or any(x.write_date > sale_order.write_date for x in mrp.workorder_ids)
                or any(y.write_date > sale_order.write_date for y in mrp.move_raw_ids)
            )
            if mrp_to_recomputes:
                sale_mrp_order_to_recomputes |= sale_order
        _logger.info(
            "Start recalculate mrp costs job for #%s sale orders." %
            len(sale_mrp_order_to_recomputes)
        )
        sale_mrp_order_to_recomputes.mapped('order_line')._compute_mrp_production_ids()
        sale_mrp_order_to_recomputes.mapped(
            'production_ids')._compute_workorder_price_subtotal()
        sale_mrp_order_to_recomputes.mapped(
            'production_ids')._compute_move_raw_price_subtotal()
        _logger.info(
            "End recalculate mrp costs job for #%s sale orders." %
            len(sale_mrp_order_to_recomputes)
        )

        # recompute actual cost and timesheet cost whenever any account.analytic.line
        # is added or changed for this sale order
        sale_analytic_order_to_recomputes = self.env["sale.order"].browse()
        for sale_order in sale_orders:
            # consider only the boms updated/created after the last write on sale order
            analytic_to_recomputes = self.env["account.analytic.line"].search([
                ("account_id", "=", sale_order.analytic_account_id.id),
                ("write_date", ">", sale_order.write_date),
            ])
            if analytic_to_recomputes:
                sale_analytic_order_to_recomputes |= sale_order

        _logger.info(
            "Start recalculate analytic costs job for #%s sale orders." %
            len(sale_analytic_order_to_recomputes)
        )
        (sale_analytic_order_to_recomputes - sale_mrp_order_to_recomputes
         ).mapped('order_line')._compute_mrp_production_ids()
        sale_analytic_order_to_recomputes._compute_analytic_cost()
        _logger.info(
            "End recalculate analytic costs job for #%s sale orders." %
            len(sale_analytic_order_to_recomputes)
        )
        (
            sale_order_to_recomputes
            | sale_analytic_order_to_recomputes
            | sale_mrp_order_to_recomputes
        ).mapped('order_line')._compute_mrp_production_total_amount()

    @api.multi
    def _recalculate_bom_costs(self):
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
