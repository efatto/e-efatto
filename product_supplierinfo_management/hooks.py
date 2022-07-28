# Copyright 2019 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def set_last_supplier_invoice_info(cr, registry):
    """
    This post-init-hook will update last price information for all products
    """
    env = api.Environment(cr, SUPERUSER_ID, dict())
    product_obj = env['product.product']
    products = product_obj.search([('purchase_ok', '=', True)])
    _logger.info('Creating #%s supplier info for products' % len(products))
    for x in range(100, len(products)+100, 100):
        products[x-100:x].set_product_last_supplier_invoice()
        _logger.info('Created %s/%s supplier info' % (x, len(products)))
    for x in range(100, len(products)+100, 100):
        products[x-100:x].set_product_last_purchase()
        _logger.info('Created %s/%s purchase info' % (x, len(products)))
