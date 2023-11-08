# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE product_template pt
        SET adjustment_cost = (
            SELECT seller.adjustment_cost FROM product_supplierinfo seller
            WHERE seller.product_tmpl_id = pt.id
            LIMIT 1
        )
        WHERE pt.id IN (
            SELECT product_tmpl_id FROM product_supplierinfo)
        """
    )
