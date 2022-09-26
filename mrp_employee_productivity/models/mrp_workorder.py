from odoo import api, fields, models


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100,
                     name_get_uid=None):
        if not name == '' and operator in ('ilike', 'like', '=', '=like', '=ilike'):
            args = [] if args is None else args.copy()
            args += [
                '|',
                ('name', operator, name),
                ('sale_id.name', operator, name),
            ]
            if operator == 'ilike':
                # to exclude extension of args with and & domain
                name = ''
        return super()._name_search(name=name, args=args, operator=operator,
                                    limit=limit, name_get_uid=name_get_uid)
