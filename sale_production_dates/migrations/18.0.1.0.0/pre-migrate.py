from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(
        env,
        [
            (
                "sale.order",
                "sale_order",
                "mrp_date_planned_finished",
                "mrp_date_finished",
            )
        ],
    )
