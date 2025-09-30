from odoo import fields, models


class HyddemoWhsListe(models.Model):
    _inherit = "hyddemo.whs.liste"

    tipo = fields.Selection(
        selection_add=[
            ("12", "Lavorazione_isola"),  # 12 scarico per lavorazione isola robot
        ],
        ondelete={"12": lambda r: r.write({"tipo": "11"})},
    )
