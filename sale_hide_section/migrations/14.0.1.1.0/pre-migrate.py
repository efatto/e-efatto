# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


def _convert_hide_to_show_details(env):
    show_details_field = [
        (
            "show_details",
            "sale.order.line.move.line",
            "sale_order_line",
            "boolean",
            False,
            "sale_hide_section",
        )
    ]
    openupgrade.add_fields(env, show_details_field)
    query = """
        UPDATE sale_order_line
        SET show_details = NOT hide_details
    """
    openupgrade.logged_query(env.cr, query)


@openupgrade.migrate()
def migrate(env, version):
    _convert_hide_to_show_details(env)
