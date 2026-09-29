from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(
        env,
        [
            (
                "mrp.production",
                "mrp_production",
                "date_planned_finished_computed",
                "date_finished_computed",
            ),
        ],
    )
