# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import time

from odoo import _, api, fields, models


class ReplenishmentCost(models.Model):
    _name = "replenishment.cost"
    _description = "Product Replenishment Cost"
    _check_company_auto = True

    name = fields.Char()
    last_update = fields.Datetime()
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    product_ctg_ids = fields.Many2many(
        comodel_name="product.category", string="Product Categories"
    )
    log = fields.Text()
    product_ids = fields.Many2many(comodel_name="product.product", check_company=True)
    products_count = fields.Integer(compute="_compute_products_count", store=True)
    missing_seller_ids = fields.Many2many(
        comodel_name="product.product",
        relation="repl_missing_seller_rel",
        column1="repl_id",
        column2="prod_id",
        string="Product missing seller",
        check_company=True,
    )
    missing_seller_price_ids = fields.Many2many(
        comodel_name="product.product",
        relation="repl_missing_price_rel",
        column1="repl_id",
        column2="prod_id",
        string="Product missing price",
        check_company=True,
    )

    @api.depends("product_ids")
    def _compute_products_count(self):
        for check in self:
            check.products_count = len(check.product_ids)

    def update_products_standard_price_and_replenishment_cost(self):
        res = self.with_context(
            update_standard_price=True,
            update_managed_replenishment_cost=True,
        ).update_products_replenishment_cost()
        return res

    def update_products_standard_price_only(self):
        res = self.with_context(
            update_standard_price=True,
        ).update_products_replenishment_cost()
        return res

    def update_products_replenishment_cost_only(self):
        res = self.with_context(
            update_managed_replenishment_cost=True,
        ).update_products_replenishment_cost()
        return res

    def update_bom_products_list_price_weight(self):
        # Update product from first bom component list price and weight
        res = self.with_context(
            update_bom_products_list_price_weight=True,
        ).update_products_replenishment_cost()
        return res

    def update_products_replenishment_cost(self):
        for repl in self:
            domain = [("type", "in", ["product", "consu", "service"])]
            if self._context.get("update_bom_products_list_price_weight"):
                domain = [("type", "=", "product"), ("bom_ids", "!=", False)]
            if repl.product_ctg_ids:
                domain.append(("categ_id", "in", repl.product_ctg_ids.ids))
            products = self.env["product.product"].search(domain)
            started_at = time.time()
            (
                products_without_seller,
                products_without_seller_price,
            ) = products.update_managed_replenishment_cost()
            duration = time.time() - started_at
            last_update = fields.Datetime.now()
            if not repl.name:
                repl.name = _("Update of %s" % last_update)
            repl.write(
                dict(
                    last_update=last_update,
                    log="Updated %s %s %s for %s products in %.2f minutes."
                    % (
                        '"standard price"'
                        if self.env.context.get("update_standard_price")
                        else "",
                        '"replenishment cost"'
                        if self.env.context.get("update_managed_replenishment_cost")
                        else "",
                        '"list price and weight"'
                        if self.env.context.get("update_bom_products_list_price_weight")
                        else "",
                        len(products),
                        duration / 60,
                    ),
                )
            )
            repl.missing_seller_ids = products_without_seller
            repl.missing_seller_price_ids = products_without_seller_price
            repl.product_ids = products
        return True

    def action_view_product_ids(self):
        self.ensure_one()
        action = self.env.ref("stock.stock_product_normal_action").read()[0]
        action.update(
            {
                "domain": [("id", "in", self.product_ids.ids)],
            }
        )
        return action
