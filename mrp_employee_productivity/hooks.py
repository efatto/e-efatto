# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.api import Environment
from odoo import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)

new_field_employee_id_added = False


def create_employee_id_equal_to_first_employee(cr):
    cr.execute("SELECT column_name FROM information_schema.columns "
               "WHERE table_name = 'mrp_workcenter_productivity' "
               "AND column_name = 'employee_id'")
    if not cr.fetchone():
        cr.execute('ALTER TABLE mrp_workcenter_productivity '
                   'ADD COLUMN employee_id INTEGER;')
        cr.execute('UPDATE mrp_workcenter_productivity '
                   'SET employee_id = ('
                   'SELECT id from hr_employee order by id limit 1);')
        global new_field_employee_id_added
        new_field_employee_id_added = True


def assign_employee_id(cr, registry):
    if not new_field_employee_id_added:
        # the field was already existing before the installation of the addon
        return
    with Environment.manage():
        env = Environment(cr, SUPERUSER_ID, {})
        productivities = env['mrp.workcenter.productivity'].search([], order="id")
        for productivity in productivities:
            user_id = productivity.user_id and productivity.user_id.id or SUPERUSER_ID
            employee_id = env['hr.employee'].search([
                ('user_id', '=', user_id)
            ], limit=1)
            if not employee_id:
                employee_id = env['hr.employee'].search([
                    ('name', '=', 'Administrator')
                ], limit=1)
            if not employee_id:
                employee_id = env['hr.employee'].search([
                ], limit=1)
            productivity.employee_id = employee_id
