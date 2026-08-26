from odoo.tools import sql


def pre_init_product_name(env):
    # set field product_template as not translatable
    cr = env.cr
    table = "product_template"
    column = "name"
    sql.convert_column_translatable(cr, table, column, "VARCHAR")
    cr.execute(
        f"""
        UPDATE {table}
        SET {column} = CONCAT(
            {column}, '_', nextval('ir_default_id_seq')
        )
        WHERE id in (
            SELECT distinct(pt.id)
            FROM {table} pt
            INNER JOIN (
                SELECT {column}, COUNT(*)
                FROM {table}
                GROUP BY {column}
                HAVING COUNT(*)>1
            ) pt1
            on pt.{column}=pt1.{column}
            or pt.{column} is NULL
            or LENGTH(pt.{column}) = 0)
        """
    )
    return True
