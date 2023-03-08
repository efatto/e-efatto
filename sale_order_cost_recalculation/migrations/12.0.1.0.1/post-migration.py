# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def set_default_purchase_date(env):
    openupgrade.logged_query(
        env.cr, """
            UPDATE sale_order_line
                SET purchase_date = write_date
            WHERE write_date is not NULL;
            """
    )


@openupgrade.migrate()
def migrate(env, version):
    set_default_purchase_date(env)
