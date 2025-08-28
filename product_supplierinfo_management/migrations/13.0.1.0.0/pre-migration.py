from openupgradelib import openupgrade


def migrate_invoice_line_values(cr, table, column):
    query = """
UPDATE {table}
SET {column} = aml.id
FROM account_invoice_line ail
WHERE aml.old_invoice_line_id = ail.id
AND aml.old_invoice_line_id = {table}.{column}
    """.format(
        table=table,
        column=column,
    )
    return openupgrade.logged_query(cr, query)


@openupgrade.migrate()
def migrate(env, installed_version):
    column = "last_supplier_invoice_line_id"
    for table in ["product_product", "product_template"]:
        openupgrade.delete_sql_constraint_safely(
            env,
            "product_supplierinfo_management",
            table,
            f"{table}_last_supplier_invoice_line_id_fkey",
        )
        migrate_invoice_line_values(env.cr, table, column)
