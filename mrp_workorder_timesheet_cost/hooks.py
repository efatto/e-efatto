import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def set_productivity_timesheet_cost(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, dict())
    productivity_obj = env['mrp.workcenter.productivity']
    productivities = productivity_obj.search([('employee_id', '!=', False)])
    _logger.info('Updating #%s productivity timesheet cost' % len(productivities))
    for x in range(100, len(productivities)+100, 100):
        for productivity in productivities[x-100:x]:
            cost = productivity.employee_id.timesheet_cost or 0.0
            amount = -productivity.duration / 60.0 * cost
            if productivity.currency_id != env.user.company_id.currency_id:
                amount = productivity.currency_id._convert(
                    amount,
                    productivity.currency_id,
                    env.user.company_id,
                    productivity.date_start)
            productivity.amount = amount
        _logger.info('Created %s/%s supplier info' % (x, len(productivities)))
