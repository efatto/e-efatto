from openupgradelib import openupgrade

from odoo.addons.product_name_unique.hook import pre_init_product_name


@openupgrade.migrate()
def migrate(env, version):
    pre_init_product_name(env.cr)
