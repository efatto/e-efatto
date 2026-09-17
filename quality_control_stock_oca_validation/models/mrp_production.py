# Copyright 2014 Serv. Tec. Avanzados - Pedro M. Baeza
# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def button_mark_done(self):
        for production in self.sudo():
            for inspection in production.qc_inspections_ids:
                if (
                    inspection.state not in ["success", "failed"]
                    and inspection.object_id.quantity > 0
                ):
                    raise ValidationError(
                        _(
                            "The manufacturing order cannot be validated as the "
                            "following quality control check are not completed: %s"
                            "\n(Refresh the page if quality control is not visible, as "
                            "it may have been created now)"
                        )
                        % inspection.name
                    )
        return super().button_mark_done()
