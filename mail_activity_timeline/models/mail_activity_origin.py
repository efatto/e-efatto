from odoo import fields, models


class MailActivityOrigin(models.Model):
    _name = 'mail.activity.origin'
    _description = 'Mail Activity Origin'
    """
    Module with name equal to origin object to group timeline
    """
    name = fields.Char(string='Name')
