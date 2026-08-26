from odoo.tools import sql


def pre_init_product_name(cr):
    # set field product_template as not translatable
    table = "product_template"
    column = "name"
    sql.convert_column_translatable(cr, table, column, "char")
    cr.execute(
        """UPDATE product_template
        SET name = CONCAT(name, '_', nextval('ir_default_id_seq'))
        WHERE id in (SELECT distinct(pt.id)
                     FROM product_template pt
                     INNER JOIN (SELECT name, COUNT(*)
                                 FROM product_template
                                 GROUP BY name
                                 HAVING COUNT(*)>1
                                 )pt1 on pt.name=pt1.name
                                  or pt.name is NULL
                                  or LENGTH(pt.name) = 0)"""
    )
    return True
