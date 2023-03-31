from odoo.tests.common import SavepointCase


class PurchaseSellerEvaluation(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_sale_order(self):
        partner = self.env["res.partner"].create({
            'name': "Customer",
        })
        activity = self.env['mail.activity'].create({
            'summary': 'Test activity on partner',
            'res_model_id': self.env["ir.model"].search([
                ("model", "=", partner._name),
            ]).id,
            'res_id': partner.id,
        })
        self.assertTrue(activity)
        new_activity = activity.action_activity_duplicate()
        self.assertTrue(new_activity)
