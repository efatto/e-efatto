import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    last_purchase_id = fields.Many2one(
        comodel_name="purchase.order",
        compute="_compute_last_purchase_line_id_info",
        string="Last Purchase",
    )
    last_purchase_discount = fields.Float(
        compute="_compute_last_purchase_line_id_info",
    )
    last_purchase_discount2 = fields.Float(
        compute="_compute_last_purchase_line_id_info",
    )
    last_purchase_discount3 = fields.Float(
        compute="_compute_last_purchase_line_id_info",
    )

    last_supplier_invoice_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="product_id",
        domain=lambda self: [
            ("parent_state", "=", "posted"),
            ("move_id.move_type", "=", "in_invoice"),
            ("product_id", "!=", False),
            ("company_id", "in", self.env.companies.ids),
        ],
        string="Last Supplier Invoice Lines",
    )
    last_supplier_invoice_line_id = fields.Many2one(
        comodel_name="account.move.line",
        compute="_compute_last_supplier_invoice_line_id",
        string="Last Supplier Invoice Line",
    )
    last_supplier_invoice_id = fields.Many2one(
        comodel_name="account.move",
        compute="_compute_last_supplier_invoice_line_id_info",
        string="Last Invoice",
    )
    last_supplier_invoice_price = fields.Float(
        compute="_compute_last_supplier_invoice_line_id_info",
        string="Invoice Unit Price",
    )
    last_supplier_invoice_discount = fields.Float(
        compute="_compute_last_supplier_invoice_line_id_info",
        string="Invoice Discount (%)",
    )
    last_supplier_invoice_discount2 = fields.Float(
        compute="_compute_last_supplier_invoice_line_id_info",
    )
    last_supplier_invoice_discount3 = fields.Float(
        compute="_compute_last_supplier_invoice_line_id_info",
    )
    last_supplier_invoice_date = fields.Date(
        compute="_compute_last_supplier_invoice_line_id_info",
    )
    last_supplier_invoice_partner_id = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_last_supplier_invoice_line_id_info",
        string="Last Invoice Supplier",
    )
    last_supplier_invoice_currency_id = fields.Many2one(
        comodel_name="res.currency",
        compute="_compute_last_supplier_invoice_line_id_info",
        string="Last Supplier Invoice Currency",
    )
    show_last_supplier_invoice_price_currency = fields.Boolean(
        compute="_compute_show_last_supplier_invoice_price_currency",
    )
    last_supplier_invoice_price_currency = fields.Float(
        string="Last currency supplier invoice price",
        compute="_compute_last_supplier_invoice_price_currency",
        digits=0,
    )

    @api.depends("last_purchase_line_ids")
    def _compute_last_purchase_line_id(self):
        # override the original method to sort by date order and not by id
        for item in self:
            last_purchase_line_id = False
            if item.last_purchase_line_ids:
                last_purchase_line_id = item.last_purchase_line_ids.sorted(
                    key=lambda l: l.order_id.date_order, reverse=True
                )[0]
            item.last_purchase_line_id = last_purchase_line_id

    @api.depends("last_purchase_line_id")
    def _compute_last_purchase_line_id_info(self):
        super()._compute_last_purchase_line_id_info()
        for item in self:
            item.last_purchase_id = item.last_purchase_line_id.order_id
            item.last_purchase_discount = item.last_purchase_line_id.discount
            item.last_purchase_discount2 = item.last_purchase_line_id.discount2
            item.last_purchase_discount3 = item.last_purchase_line_id.discount3

    @api.depends("last_supplier_invoice_line_ids")
    def _compute_last_supplier_invoice_line_id(self):
        for item in self:
            last_supplier_invoice_line_id = False
            if item.last_supplier_invoice_line_ids:
                last_supplier_invoice_line_id = (
                    item.last_supplier_invoice_line_ids.sorted(
                        key=lambda l: l.move_id.invoice_date, reverse=True
                    )[0]
                )
            item.last_supplier_invoice_line_id = last_supplier_invoice_line_id

    @api.depends("last_supplier_invoice_line_id")
    def _compute_last_supplier_invoice_line_id_info(self):
        for item in self:
            item.last_supplier_invoice_price = (
                item.last_supplier_invoice_line_id.price_unit
            )
            item.last_supplier_invoice_date = (
                item.last_supplier_invoice_line_id.move_id.invoice_date
            )
            item.last_supplier_invoice_currency_id = (
                item.last_supplier_invoice_line_id.currency_id
            )
            item.last_supplier_invoice_discount = (
                item.last_supplier_invoice_line_id.discount
            )
            item.last_supplier_invoice_discount2 = (
                item.last_supplier_invoice_line_id.discount2
            )
            item.last_supplier_invoice_discount3 = (
                item.last_supplier_invoice_line_id.discount3
            )
            item.last_supplier_invoice_partner_id = (
                item.last_supplier_invoice_line_id.partner_id
            )
            item.last_supplier_invoice_id = item.last_supplier_invoice_line_id.move_id

    @api.depends("last_supplier_invoice_line_id", "last_supplier_invoice_currency_id")
    def _compute_show_last_supplier_invoice_price_currency(self):
        for item in self:
            last_line = item.last_supplier_invoice_line_id
            item.show_last_supplier_invoice_price_currency = (
                last_line
                and item.last_supplier_invoice_currency_id
                and item.last_supplier_invoice_currency_id
                != last_line.company_id.currency_id
            )

    @api.depends(
        "last_supplier_invoice_line_id",
        "show_last_supplier_invoice_price_currency",
        "last_supplier_invoice_currency_id",
        "last_supplier_invoice_date",
    )
    def _compute_last_supplier_invoice_price_currency(self):
        for item in self:
            if item.show_last_supplier_invoice_price_currency:
                rates = item.last_supplier_invoice_currency_id._get_rates(
                    item.last_supplier_invoice_line_id.company_id,
                    item.last_supplier_invoice_date,
                )
                item.last_supplier_invoice_price_currency = rates.get(
                    item.last_supplier_invoice_currency_id.id
                )
            else:
                item.last_supplier_invoice_price_currency = 1
