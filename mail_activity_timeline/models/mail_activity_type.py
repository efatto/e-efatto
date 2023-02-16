from odoo import fields, models


class MailActivityType(models.Model):
    _inherit = 'mail.activity.type'

    is_resource_planner = fields.Boolean()

    _sql_constraints = [
        (
            "activity_planner_type_unique",
            "UNIQUE (res_model_id, is_resource_planner)",
            "Another planner activity type exists for the linked res model.",
        ),
    ]

    # aggiungere un blocco all'eliminazione del tipo attività per il modello? essendo
    # le attività create in automatico da dopo l'installazione, pare abbastanza
    # difficile che succeda
