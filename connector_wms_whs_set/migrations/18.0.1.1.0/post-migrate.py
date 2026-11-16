from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    production_sets = env["mrp.production.set"].search([])
    if production_sets:
        # recompute the stored state to show "sent_to_whs" on sets whose linked
        # productions were already sent to WHS before this module version
        env.add_to_compute(
            production_sets._fields["state"],
            production_sets,
        )
