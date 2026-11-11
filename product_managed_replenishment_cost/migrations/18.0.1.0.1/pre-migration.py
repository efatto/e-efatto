from openupgradelib import openupgrade
from psycopg2 import sql


def _convert_column_to_company_dependent(env, model_name, field_name):
    """Turn a plain stored column into a company dependent jsonb column.

    Reusable helper for a field that becomes ``company_dependent=True`` in
    17.0/18.0 without having lived in ``ir_property`` before (openupgradelib's
    ``convert_to_company_dependent`` only handles the ``ir_property`` storage
    removed in 17.0). Safe to run more than once: it does nothing if the
    column is missing or already ``jsonb``.

    :param env: Odoo environment
    :param model_name: name of the model owning the field
    :param field_name: name of the field/column to convert
    """
    cr = env.cr
    table = env[model_name]._table
    if not openupgrade.column_exists(cr, table, field_name):
        # the column does not exist yet: Odoo will create it as jsonb
        return
    cr.execute(
        """
        SELECT data_type
          FROM information_schema.columns
         WHERE table_schema = current_schema()
           AND table_name = %s
           AND column_name = %s
        """,
        (table, field_name),
    )
    row = cr.fetchone()
    if not row or row[0] == "jsonb":
        # already company dependent, nothing to do
        return
    cr.execute("SELECT id FROM res_company ORDER BY id")
    company_ids = [str(company_id) for (company_id,) in cr.fetchall()]
    if not company_ids:
        # no company found: let Odoo create the column as jsonb
        return
    pairs = sql.SQL(", ").join(
        # all the companies get the current value of the column
        sql.SQL("{}, {}").format(sql.Literal(company_id), sql.Identifier(field_name))
        for company_id in company_ids
    )
    openupgrade.logged_query(
        cr,
        sql.SQL(
            "ALTER TABLE {table} ALTER COLUMN {column} TYPE jsonb "
            "USING jsonb_build_object({pairs})"
        ).format(
            table=sql.Identifier(table),
            column=sql.Identifier(field_name),
            pairs=pairs,
        ),
    )


@openupgrade.migrate()
def migrate(env, version):
    """Make product.product.direct_cost company dependent.

    In 18.0 the field is company dependent, so it is stored as a jsonb
    mapping of company id to value (e.g. ``{"1": 12.5}``), while in 14.0 it
    was a plain stored float (a ``numeric`` column). Odoo's automatic
    ``direct_cost::jsonb`` cast fails with "cannot cast type numeric to
    jsonb", so the column is converted explicitly. The helper does nothing
    if the column is missing or already ``jsonb``.
    """
    _convert_column_to_company_dependent(env, "product.product", "direct_cost")
