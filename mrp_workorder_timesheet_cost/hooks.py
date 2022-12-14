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
            productivity.amount = productivity.employee_id.timesheet_cost * \
                productivity.duration / 60.0
        _logger.info('Created %s/%s supplier info' % (x, len(productivities)))
