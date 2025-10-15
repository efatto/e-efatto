from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(
        env,
        [
            (
                'sale.order',
                'sale_order',
                'extra_cost',
                'actual_cost_mrp',
            ),
        ]
    )
