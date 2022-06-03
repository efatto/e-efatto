# -*- coding: utf-8 -*-
# Copyright 2012-2016 Camptocamp SA
# Copyright 2019 Tecnativa
# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, date
from odoo.tools.date_utils import relativedelta
from odoo import api, fields, models


class Orderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    orderpoint_tmpl_id = fields.Many2one(
        'stock.warehouse.orderpoint.template'
    )


class OrderpointTemplate(models.Model):
    _inherit = 'stock.warehouse.orderpoint.template'

    # product_id = fields.Many2one(
    #     domain=[('type', '!=', 'service')]
    # ) # direi inutile, i consu non sono ordinabili no?
    auto_min_qty_criteria = fields.Selection(
        selection_add=[
            ('rule', 'Rule'),
        ],
    )
    auto_max_qty_criteria = fields.Selection(
        selection_add=[
            ('rule', 'Rule'),
        ],
    )
    variable_period = fields.Boolean(
        'Compute on variable time period',
        default=True,
        help='Compute rules on a bunch of time, e.g. "Last 90 days".')
    product_ctg_id = fields.Many2one('product.category', string='Product Category')
    max_min_rule_ids = fields.One2many(
        'orderpoint.template.rule', 'orderpoint_tmpl_id', string='Rules')

    def _check_product_uom(self):
        for rule in self:
            if rule.product_id:
                if rule.product_id.uom_id.category_id.id != \
                        rule.product_uom.category_id.id:
                    return False
        return True

    _constraints = [
        (_check_product_uom,
         'You have to select a product unit of measure in the same '
         'category than the default unit of measure of the product',
         ['product_id', 'product_uom']),
    ]

    def _template_fields_to_discard(self):
        """In order to create every orderpoint we should pop this template
           customization fields """
        return [
            'auto_generate', 'auto_product_ids', 'auto_last_generation',
            'auto_min_qty', 'auto_min_date_start', 'auto_min_qty_criteria',
            'auto_min_date_end', 'auto_max_date_start', 'auto_max_date_end',
            'auto_max_qty_criteria', 'auto_max_qty', 'product_ctg_id',
        ]

    def _disable_old_instances(self, products):
        """Clean old instance by setting those inactives"""
        # extend product list with the 'end' state as they are excluded by default
        # but if state is changed the op will never be removed
        extended_products = self.env['product.product'].search([
            '|', ('id', 'in', products.ids),
            ('state', '=', 'end'),
        ])
        orderpoints = self.env['stock.warehouse.orderpoint'].search(
            [('product_id', 'in', extended_products.ids)]
        )
        orderpoints.write({'active': False})

    @api.model
    def _get_product_qty_by_rules(
            self, products, location_id, from_date, to_date, rule):
        """Returns a dict with product ids as keys and the resulting
           calculation of historic moves according to criteria"""
        stock_qty_history = products._compute_historic_quantities_dict(
                location_id=location_id,
                from_date=from_date,
                to_date=to_date,
                rule=rule)
        if not stock_qty_history:
            return False
        return {x: {'min_qty': y['min_qty'],
                    'max_qty': y['max_qty'],
                    'product_uom': y['product_uom']}
                for x, y in stock_qty_history.items()}

    def _create_instances(self, product_ids):
        """Create instances of model using template inherited model and
           compute autovalues if needed"""
        orderpoint_model = self.env['stock.warehouse.orderpoint']
        for template_op in self:
            for data in template_op.copy_data():
                for discard_field in self._template_fields_to_discard():
                    data.pop(discard_field)
            for rule in template_op.max_min_rule_ids:
                date_start = date.today() + relativedelta(days=-rule.move_days)
                date_end = date.today()
                stock_qty = (
                    self._get_product_qty_by_rules(
                        product_ids,
                        location_id=template_op.location_id.id,
                        from_date=date_start,
                        to_date=date_end,
                        rule=rule,
                    ))
                if not stock_qty:
                    continue
                for product_id in product_ids:
                    vals = data.copy()
                    vals['name'] = '%s [%s days]' % (vals['name'], rule.move_days)
                    vals['product_id'] = product_id.id
                    vals['orderpoint_tmpl_id'] = template_op.id
                    vals['product_uom'] = stock_qty.get(product_id.id, 0).get(
                        'product_uom')
                    if template_op.auto_min_qty:
                        vals['product_min_qty'] = stock_qty.get(
                            product_id.id, 0).get('min_qty', 0)
                    if template_op.auto_max_qty:
                        vals['product_max_qty'] = stock_qty.get(
                            product_id.id, 0).get('max_qty', 0)
                    # only if rules have at least one qty >0
                    if vals.get('product_max_qty', 0) > 0 \
                            or vals.get('product_min_qty', 0) > 0:
                        # todo delete orderpoint_model created for the same product
                        to_delete_orderpoint_ids = orderpoint_model.search(
                            [('product_id', '=', product_id.id)]
                        )
                        if to_delete_orderpoint_ids:
                            to_delete_orderpoint_ids.unlink()
                        orderpoint_model.create(vals)

    @api.multi
    def create_orderpoints(self, products):
        """ Create orderpoint for *products* based on these templates.
        type products: recordset of products
        """
        self._disable_old_instances(products)
        self._create_instances(products)

    @api.multi
    def create_auto_orderpoints(self):
        for template_op in self:
            if not template_op.auto_generate:
                continue
            if (not template_op.auto_last_generation or
                    template_op.write_date > template_op.auto_last_generation):
                template_op.auto_last_generation = datetime.now()
                product_ids = template_op.auto_product_ids
                domain = [('state', '!=', 'end')]
                if template_op.product_ctg_id:
                    domain.append(('categ_id', '=', template_op.product_ctg_id.id))
                if template_op.product_ctg_id:
                    product_ids = self.env['product.product'].search(domain)

                template_op.create_orderpoints(product_ids)


class OrderpointTemplateRule(models.Model):
    _name = 'orderpoint.template.rule'
    _description = 'Orderpoint Template Rule'
    _order = "sequence asc"

    name = fields.Char(
        compute='compute_name', store=True
    )
    orderpoint_tmpl_id = fields.Many2one(
        'stock.warehouse.orderpoint.template',
        string='Ordepoint Template',
        required=True)
    min_move_qty = fields.Float('Minimum customer moved Qty')
    max_move_qty = fields.Float('Maximum customer moved Qty')
    min_orderpoint_qty = fields.Float('Minimum orderpoint Qty')
    max_orderpoint_qty = fields.Float('Maximum orderpoint Qty')
    sequence = fields.Integer('Sequence', default=1)
    move_days = fields.Integer(
        'Days of customer moves',
        help='Period of time on which are computed the conditions of the rule. '
             'Priority will be given to rule with less sequence value (viewed on top '
             'by default).')

    @api.multi
    @api.depends('move_days')
    def compute_name(self):
        for record in self:
            record.name = '%s [%s days]' % (
                record.orderpoint_tmpl_id.name, record.move_days)
