

def copy_expected_qty(cr, registry):
    cr.execute('UPDATE stock_move SET expected_product_uom_qty = product_uom_qty '
               'WHERE bom_line_id IS NOT NULL')
