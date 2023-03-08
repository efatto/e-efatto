# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # inserire nel campo lead_line_id nel PO la prima riga del lead collegato all'SO
    if not openupgrade.column_exists(env.cr, 'purchase_order', 'lead_line_id'):
        openupgrade.add_fields(
            env,
            [('lead_line_id', 'purchase.order', 'purchase_order', 'many2one',
              False, 'purchase_sale_mrp_link')]
        )
        env.cr.execute("""
            UPDATE purchase_order po
            SET lead_line_id = (
                SELECT cll.id
                FROM sale_order so
                LEFT JOIN sale_order_purchase_order_rel so_po ON so.id = so_po.sale_id
                LEFT JOIN crm_lead cl ON cl.id = so.opportunity_id
                LEFT JOIN crm_lead_line cll ON cll.lead_id = cl.id
                WHERE po.id = so_po.purchase_id
                LIMIT 1
            )
        """)
