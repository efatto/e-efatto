# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.report_py3o.models import _py3o_parser_context


def display_address(address_record, without_company=False):
    res = address_record._display_address(without_company=without_company)
    while "\n\n" in res:
        res = res.replace('\n\n ', '\n').replace('\n\n', '\n')
    return res

_py3o_parser_context.display_address = display_address
