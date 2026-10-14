from openupgradelib import openupgrade
from openupgradelib.openupgrade_180 import convert_column_to_company_dependent


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
    convert_column_to_company_dependent(env, "product.product", "direct_cost")
