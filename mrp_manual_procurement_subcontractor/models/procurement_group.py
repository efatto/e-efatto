from odoo import api, models
from odoo.tools import config


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    @api.model
    def run(self, product_id, product_qty, product_uom, location_id, name,
            origin, values):
        if not config['test_enable'] or self.env.context.get(
            'test_mrp_manual_procurement_subcontractor'
        ):
            if self.env.context.get('is_stopped'):
                # do nothing
                return True

        return super(ProcurementGroup, self).run(product_id, product_qty,
                                                 product_uom, location_id,
                                                 name, origin, values)


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _make_po_select_supplier(self, values, suppliers):
        supplier = super()._make_po_select_supplier(values=values, suppliers=suppliers)
        if self.env.context.get("subcontractor_id"):
            subcontractor_id = self.env.context.get("subcontractor_id")
            subcontractor_supplier = suppliers.filtered(
                lambda x: x.name == subcontractor_id)
            if subcontractor_supplier:
                supplier = subcontractor_supplier
        return supplier
