# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def split_discount_to_triple(env):
    openupgrade.logged_query(
        env.cr, """
            UPDATE account_invoice_line 
                SET 
                discount = (string_to_array(complex_discount, '+'))[1]::numeric,
                discount2 = (string_to_array(complex_discount, '+'))[2]::numeric,
                discount3 = (string_to_array(complex_discount, '+'))[3]::numeric
                WHERE complex_discount is not null;
            """
    )


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(
        env.cr, 'account_invoice_line', 'complex_discount',
    ):
        split_discount_to_triple(env)
