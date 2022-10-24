# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models, _
from odoo.exceptions import UserError


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.multi
    def _prepare_purchase_requisition_line(
            self, product_id, product_qty, product_uom, values, pr):
        return {
            'requisition_id': pr.id,
            'product_id': product_id.id,
            'product_uom_id': product_uom.id,
            'product_qty': product_qty,
            'move_dest_id': values.get('move_dest_ids')
            and values['move_dest_ids'][0].id or False,
        }

    @api.multi
    def _run_buy(self, product_id, product_qty, product_uom, location_id, name, origin,
                 values):
        if product_id.purchase_requisition != 'tenders':
            return super(StockRule, self)._run_buy(
                product_id, product_qty, product_uom, location_id, name, origin, values)
        # Check if exists a purchase requisition in state draft with the same first
        #  supplier of current product of the existing product and append line to it
        supplier_partner_id = product_id.default_supplier_partner_id
        if not supplier_partner_id:
            suppliers = product_id.seller_ids\
                .filtered(lambda r: (
                    not r.company_id or r.company_id == values['company_id'])
                    and (not r.product_id or r.product_id == product_id)
                    and r.name.active)
            if not suppliers:
                msg = _('There is no vendor associated to the product %s. '
                        'Please define a vendor for this product.') % \
                      product_id.display_name
                raise UserError(msg)
            else:
                supplier_partner_id = suppliers[0].name

        domain = (
            ('state', '=', 'draft'),
            ('company_id', '=', values.get('company_id') and values['company_id'].id
                or self.env.user.company_id.id),
            ('line_ids.product_id.seller_ids.name', 'in', supplier_partner_id.ids),
            ('origin', '=', origin),
        )
        # fixme: aggiungere conto analitico alla riga creata (chi lo fa adesso? att.ne
        #  che non risulti in un doppione, di default non dovrebbe metterlo no?)
        pr = self.env['purchase.requisition'].sudo().search(domain)
        pr = pr[0] if pr else False
        if not pr:
            vals = self.env['purchase.requisition']._prepare_tender_values(
                product_id, product_qty, product_uom, location_id, name, origin, values)
            company_id = values.get('company_id') and values['company_id'].id \
                or self.env.user.company_id.id
            self.env['purchase.requisition'].with_context(
                force_company=company_id).sudo().create(vals)
        else:
            # Only ability to create Line in existing purchase requisition
            vals = self._prepare_purchase_requisition_line(
                product_id, product_qty, product_uom, values, pr)
            self.env['purchase.requisition.line'].sudo().create(vals)
        return True
