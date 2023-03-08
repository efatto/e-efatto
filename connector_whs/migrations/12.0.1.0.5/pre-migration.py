# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade

_column_renames = {
    'hyddemo_whs_liste': [
        ('picking', None),
    ],
}


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    if openupgrade.column_exists(cr, 'hyddemo_whs_liste', 'picking'):
        openupgrade.rename_columns(cr, _column_renames)
