# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    compute_pricelist_on_bom_component = fields.Boolean(
        string="Price from BOM",
        help="Compute price on pricelist rules of component of bom, generating a total "
             "price mixing multiple rules.")


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_bom_price(self, pricelist, bom, quantity, partner, date=False, uom_id=False,
                      boms_to_recompute=False):
        self.ensure_one()
        if not bom:
            return 0
        if not boms_to_recompute:
            boms_to_recompute = []
        total = 0
        operation_total_price = 0
        rule_obj = self.env['product.pricelist.item']
        for opt in bom.bom_operation_ids:
            res = pricelist._compute_price_rule([(opt.product_id, opt.time, partner)])
            rule = rule_obj.browse(res[opt.product_id.id][1])
            operation_total_price += \
                opt.time * \
                rule._compute_price(
                    opt.price_unit, opt.product_id.uom_id, opt.product_id)
        total += operation_total_price
        # group cost of components by listprice categories defined in pricelist
        # to compute prices on brackets
        listprice_categ_ids = pricelist.mapped('item_ids.listprice_categ_id')
        for listprice_categ_id in listprice_categ_ids:
            bom_lines = bom.bom_line_ids.filtered(
                lambda x: x.product_id.categ_id.listprice_categ_id ==
                listprice_categ_id
            )
            bom_lines_cost = 0
            for line in bom_lines:
                if line._skip_bom_line(self):
                    continue
                if not line.price_unit:
                    raise ValidationError(_('Missing cost in bom line for product %s!'
                                            ) % line.product_id.name)
                # Compute recursive if line has `child_line_ids`
                if line.child_bom_id and line.child_bom_id in boms_to_recompute:
                    # check all component of child bom are in the same listprice
                    # category
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
            for rule in pricelist.item_ids.filtered(
                lambda x: x.listprice_categ_id == listprice_categ_id
            ):
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
            total += price
        return bom.product_uom_id._compute_price(
                total / (bom.product_qty or 1), self.uom_id)
