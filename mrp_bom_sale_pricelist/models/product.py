# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    compute_pricelist_on_bom_component = fields.Boolean(
        string="Price from BOM",
        help="Compute price on pricelist rules of component of bom, generating a total "
             "price mixing multiple rules.")


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_listprice_categ_id(self, categ_id):
        product_listprice_categ_id = categ_id.listprice_categ_id
        if not product_listprice_categ_id and categ_id.parent_id:
            product_listprice_categ_id = self._get_listprice_categ_id(categ_id.parent_id)
        return product_listprice_categ_id

    def get_bom_operation_price(self, pricelist, bom, quantity, partner, date=False,
                                uom_id=False, boms_to_recompute=False,
                                total_to_exclude_from_global_rule=0):
        self.ensure_one()
        if not bom:
            return 0
        if not boms_to_recompute:
            boms_to_recompute = []
        total = 0
        global_rules = pricelist.item_ids.filtered(
            lambda x: not x.listprice_categ_id and x.applied_on == '3_global'
            and x.base == 'pricelist' and x.base_pricelist_id
        )
        # group cost of components by listprice categories defined in pricelist
        # to compute prices on brackets
        listprice_categ_ids = pricelist.mapped('item_ids.listprice_categ_id')
        operation_prices = {}
        for opt in bom.bom_operation_ids:
            listprice_ctg = self._get_listprice_categ_id(opt.product_id.categ_id)
            if listprice_ctg not in operation_prices:
                operation_prices.update({listprice_ctg: {}})
        for opt in bom.bom_operation_ids:
            listprice_categ_id = self._get_listprice_categ_id(
                opt.product_id.categ_id)
            if not opt.price_unit:
                raise ValidationError(_('Missing cost in bom line for product %s!'
                                        ) % opt.product_id.name)
            if opt not in operation_prices[listprice_categ_id]:
                operation_prices[listprice_categ_id].update({
                    opt: opt.time
                })
        for listprice_categ_id in listprice_categ_ids:
            price = 0
            base_pricelist_rule_found = bool(any(
                [x.base == 'pricelist' and x.base_pricelist_id
                 for x in pricelist.item_ids]))
            for rule in pricelist.item_ids:
                if rule.base == 'pricelist' and rule.base_pricelist_id:
                    price += self.get_bom_operation_price(
                        rule.base_pricelist_id, bom, quantity, partner, date, uom_id,
                        boms_to_recompute, total_to_exclude_from_global_rule)
                    continue
                if rule.listprice_categ_id != listprice_categ_id:
                    continue
                if listprice_categ_id in operation_prices:
                    operation_price = operation_prices[listprice_categ_id]
                    price += sum([
                        operation_price[operation] *
                        rule._compute_price(
                            operation.price_unit, operation.product_id.uom_id,
                            operation.product_id)
                        for operation in operation_price])
                if base_pricelist_rule_found:
                    total_to_exclude_from_global_rule += price
            if all([x.listprice_categ_id != listprice_categ_id for x in
                    pricelist.item_ids]):
                # there aren't applicable rules of type listprice category for current
                # product in this pricelist, so use normal function to find rule to
                # compute price
                product_context = dict(
                    self.env.context, partner_id=partner.id, date=date, uom=uom_id)
                for operation in operation_price:  # FIXME
                    fake_price, rule_id = pricelist.with_context(
                        product_context).get_product_price_rule(
                            operation.product_id, quantity, partner)
                    rule = self.env['product.pricelist.item'].browse(rule_id)
                    price = rule._compute_price(
                        price, operation.product_id.uom_id, operation.product_id
                    )
            total += price
        for global_rule in global_rules:
            total = global_rule._compute_price(
                total - total_to_exclude_from_global_rule, self.uom_id, self
            )
            total += total_to_exclude_from_global_rule
        return bom.product_uom_id._compute_price(
            total / (bom.product_qty or 1), self.uom_id)

    def get_bom_price(self, pricelist, bom, quantity, partner, date=False, uom_id=False,
                      boms_to_recompute=False, total_to_exclude_from_global_rule=0):
        self.ensure_one()
        if not bom:
            return 0
        if not boms_to_recompute:
            boms_to_recompute = []
        total = 0
        global_rules = pricelist.item_ids.filtered(
            lambda x: not x.listprice_categ_id and x.applied_on == '3_global'
            and x.base == 'pricelist' and x.base_pricelist_id
        )
        # group cost of components by listprice categories defined in pricelist
        # to compute prices on brackets
        listprice_categ_ids = pricelist.mapped('item_ids.listprice_categ_id')
        for listprice_categ_id in listprice_categ_ids:
            bom_lines_cost = 0
            for line in bom.bom_line_ids:
                line_product_listprice_categ_id = self._get_listprice_categ_id(
                    line.product_id.categ_id)
                if line_product_listprice_categ_id != listprice_categ_id:
                    continue
                if line._skip_bom_line(self):
                    continue
                if not line.price_unit:
                    raise ValidationError(_('Missing cost in bom line for product %s!'
                                            ) % line.product_id.name)
                # Compute recursive if line has `child_line_ids`
                if line.child_bom_id and line.child_bom_id in boms_to_recompute:
                    # check all component of child bom are in the same listprice
                    # category FIXME questo non va più visto che usiamo le ctg padri
                    if any([x.listprice_categ_id != listprice_categ_id for x in
                            line.child_bom_id.mapped(
                                'bom_line_ids.product_id.categ_id.listprice_categ_id')]):
                        raise ValidationError(_(
                            'Some product of child bom for product %s have a different '
                            'listiprice category!') % line.product_id.name)
                    child_total = line.product_id.get_bom_price(
                        pricelist, line.child_bom_id, line.product_qty,
                        partner, boms_to_recompute=boms_to_recompute)
                    bom_lines_cost += child_total * line.product_qty
                else:
                    bom_lines_cost += line.price_unit * line.product_qty
            # integrato qui una funzione di calcolo del prezzo sulle regole applicabili
            # basato sul valore totale per categoria
            price = 0
            base_pricelist_rule_found = bool(any(
                [x.base == 'pricelist' and x.base_pricelist_id
                 for x in pricelist.item_ids]))
            for rule in pricelist.item_ids:
                if rule.base == 'pricelist' and rule.base_pricelist_id:
                    price += self.get_bom_price(
                        rule.base_pricelist_id, bom, quantity, partner, date, uom_id,
                        boms_to_recompute, total_to_exclude_from_global_rule)
                    continue
                if rule.listprice_categ_id != listprice_categ_id:
                    continue
                if bom_lines_cost < rule.min_value:
                    continue
                if rule.min_value <= bom_lines_cost and (
                        rule.max_value and (bom_lines_cost < rule.max_value)
                        or True):
                    value = min(
                            bom_lines_cost - rule.min_value,
                            rule.max_value and (rule.max_value - rule.min_value) or
                            bom_lines_cost - rule.min_value
                        )
                    if value > 0:
                        price += rule._compute_price(
                            value, self.uom_id, self)
                        if base_pricelist_rule_found:
                            total_to_exclude_from_global_rule += price
            total += price

        for global_rule in global_rules:
            total = global_rule._compute_price(
                total - total_to_exclude_from_global_rule, self.uom_id, self
            )
            total += total_to_exclude_from_global_rule
        return bom.product_uom_id._compute_price(
                total / (bom.product_qty or 1), self.uom_id)
