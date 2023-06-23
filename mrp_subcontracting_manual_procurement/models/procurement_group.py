from odoo import api, models
from odoo.tools import config


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    @api.model
    def run(self, product_id, product_qty, product_uom, location_id, name,
            origin, values):
        if not config['test_enable'] or self.env.context.get(
            'test_mrp_subcontracting_manual_procurement'
        ):
            if self.env.context.get('is_procurement_stopped'):
                # do nothing
                return True

        return super(ProcurementGroup, self).run(product_id, product_qty,
                                                 product_uom, location_id,
                                                 name, origin, values)


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _make_po_select_supplier(self, values, suppliers):
        """ Method intended to be overridden by customized modules to implement any
            logic in the selection of supplier.
        """
        supplier = super()._make_po_select_supplier(values=values, suppliers=suppliers)
        orderpoint_id = values.get('orderpoint_id')
        if orderpoint_id:
            product_id = orderpoint_id.product_id
            # get stock moves that created this orderpoint request
            if product_id and any(x.is_subcontractor for x in suppliers):
                stock_move_ids = self.env['stock.move'].search([
                    ('state', '=', 'confirmed'),
                    ('product_id', '=', product_id.id),
                    ('raw_material_production_id', '!=', False),
                ])
                subcontractors = stock_move_ids.mapped('subcontractor_id')
                if subcontractors:
                    # select the first of subcontractors in stock moves found in
                    # productions
                    subcontractor = subcontractors[0]
                    supplier = suppliers.filtered(lambda x: x.name == subcontractor)
        return supplier
