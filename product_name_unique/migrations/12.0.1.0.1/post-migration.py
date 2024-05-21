# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def drop_sql_constraint(env):
    openupgrade.logged_query(
        env.cr, """
            ALTER TABLE product_template
                DROP CONSTRAINT product_template_name_uniq;
            """
    )


@openupgrade.migrate()
def migrate(env, version):
    drop_sql_constraint(env)
