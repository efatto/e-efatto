from odoo.tools import SQL, sql


def pre_init_product_name(env):
    # set field product_template as not translatable
    cr = env.cr
    table = "product_template"
    column = "name"
    sql.drop_index(cr, "product_template_name_index", table)
    sql.convert_column_translatable(cr, table, column, "VARCHAR")
    cr.execute(
        SQL(
            """
        UPDATE %(table)s
        SET %(column)s = CONCAT(
            %(column)s, '_', nextval(%(sequence)s)
        )
        WHERE id in (
            SELECT distinct(pt.id)
            FROM %(table)s pt
            INNER JOIN (
                SELECT %(column)s, company_id, COUNT(*)
                FROM %(table)s
                GROUP BY %(column)s, company_id
                HAVING COUNT(*)>1
            ) pt1
            on pt.%(column)s=pt1.%(column)s
            and pt.company_id is not distinct from pt1.company_id
            or pt.%(column)s is NULL
            or LENGTH(pt.%(column)s) = 0)
        """,
            table=SQL.identifier(table),
            column=SQL.identifier(column),
            sequence="ir_default_id_seq",
        )
    )
    return True
