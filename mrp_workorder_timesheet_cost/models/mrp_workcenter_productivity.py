from odoo import api, fields, models


class MrpWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    currency_id = fields.Many2one(
        related='employee_id.currency_id',
        readonly=True)
    amount = fields.Monetary('Amount', required=True, default=0.0)

    @api.model
    def create(self, values):
        result = super().create(values)
        if result.employee_id:
            result._productivity_postprocess(values)
        return result

    @api.multi
    def write(self, values):
        result = super().write(values)
        self.filtered(lambda x: x.employee_id)._productivity_postprocess(values)
        return result

    @api.multi
    def _productivity_postprocess(self, values):
        """ 
        Hook to update record one by one according to the values of a `write` 
        or a `create`. 
        """
        sudo_self = self.sudo()
        # this creates only one env for all operation that required sudo() 
        # in `_productivity_postprocess_values`override
        values_to_write = self._productivity_postprocess_values(values)
        for productivity in sudo_self:
            if values_to_write[productivity.id]:
                productivity.write(values_to_write[productivity.id])
        return values

    @api.multi
    def _productivity_postprocess_values(self, values):
        """ Get the addionnal values to write on record
            :param dict values: values for the model's fields, as a dictionary::
                {'field_name': field_value, ...}
            :return: a dictionary mapping each record id to its corresponding
                dictionnary values to write (may be empty).
        """
        result = {id_: {} for id_ in self.ids}
        sudo_self = self.sudo()
        # (re)compute the amount (depending on duration and employee_id for the cost)
        # currency_id is related to employee_id so should never be here - to check
        if any([field_name in values for field_name in ['duration', 'employee_id']]):
            for productivity in sudo_self:
                cost = productivity.employee_id.timesheet_cost or 0.0
                amount = -productivity.duration / 60.0 * cost
                if productivity.currency_id != self.env.user.company_id.currency_id:
                    amount = productivity.currency_id._convert(
                        amount,
                        productivity.currency_id,
                        self.env.user.company_id,
                        productivity.date_start)
                result[productivity.id].update({
                    'amount': amount,
                })
        return result
