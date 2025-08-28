from openupgradelib import openupgrade
from psycopg2 import sql


def drop_constraint(cr, table, column):
    drop_sql = sql.SQL("ALTER TABLE {} DROP CONSTRAINT {}")
    cr.execute(
        """
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE constraint_type = 'FOREIGN KEY' AND table_name = %s
            AND constraint_name like %s
        """,
        (table, "%%%s%%" % column),
    )
    for constraint in (row[0] for row in cr.fetchall()):
        openupgrade.logged_query(
            cr,
            drop_sql.format(
                sql.Identifier(table),
                sql.Identifier(constraint),
            ),
        )


def migrate_invoice_line_values(cr, table, column):
    query = """
UPDATE {table}
SET {column} = aml.id
FROM account_move_line aml
WHERE aml.old_invoice_line_id = {table}.{column}
    """.format(
        table=table,
        column=column,
    )
    return openupgrade.logged_query(cr, query)


def migrate(cr, installed_version):
    column = "last_supplier_invoice_line_id"
    for table in ["product_product", "product_template"]:
        drop_constraint(cr, table, column)
        migrate_invoice_line_values(cr, table, column)
