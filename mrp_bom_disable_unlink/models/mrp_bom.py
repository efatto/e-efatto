
from odoo import api, models, _
from odoo.exceptions import UserError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.multi
    def unlink(self):
        if self.env['mrp.production'].search([('bom_id', 'in', self.ids)], limit=1):
            raise UserError(_('You can not delete a Bill of Material used in '
                              'manufacturing orders.'))
        return super(MrpBom, self).unlink()
