import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    sales = env['sale.order'].search([])
    i_max = len(sales)
    i = 0
    for sale in sales:
        i += 1
        sale._compute_analytic_cost()
        # force compute of dependings fields - done only by user usually
        sale.order_line._compute_mrp_production_total_amount()
        _logger.info('Recomputed analytic cost for sale order #%s/%s' % (
            i, i_max
        ))
