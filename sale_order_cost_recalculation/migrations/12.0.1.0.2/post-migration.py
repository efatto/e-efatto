# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def set_purchase_date_from_price_history(env):
    # set date cost accordingly to price history
    openupgrade.logged_query(
        env.cr, """
            UPDATE sale_order_line sol
                SET purchase_date = (
                    SELECT pph.datetime FROM product_price_history pph
                    WHERE pph.product_id = sol.product_id
                    AND pph.cost = sol.purchase_price
                    AND pph.datetime <= sol.write_date
                    ORDER BY pph.datetime DESC
                    LIMIT 1
                )
            ;
            """
    )


def set_product_date_from_price_history(env):
    # set date accordingly to price history
    openupgrade.logged_query(
        env.cr, """
            UPDATE product_product pp
                SET standard_price_write_date = (
                    SELECT pph.datetime FROM product_price_history pph
                    WHERE pph.product_id = pp.id
                    AND pph.datetime <= pp.write_date
                    ORDER BY pph.datetime DESC
                    LIMIT 1
                )
            ;
            """
    )


@openupgrade.migrate()
def migrate(env, version):
    set_purchase_date_from_price_history(env)
    set_product_date_from_price_history(env)
