from openupgradelib import openupgrade, openupgrade_180


@openupgrade.migrate()
def migrate(env, version):
    """Move the values of the already company-dependent fields to jsonb."""
    openupgrade_180.convert_company_dependent(env, "product.product", "adjustment_cost")
    openupgrade_180.convert_company_dependent(env, "product.product", "landed_cost")
