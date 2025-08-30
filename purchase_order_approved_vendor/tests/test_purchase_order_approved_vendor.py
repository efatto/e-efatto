from odoo.tests.common import SavepointCase


class PurchaseAutocompleteQtyToInvoice(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_selection_order(self):
        purchase_order = self.env["purchase.order"]
        selection = purchase_order._fields["state"].selection
        self.assertEqual(
            selection,
            [
                ("draft", "RFQ"),
                ("rfq sent", "RFQ Sent"),
                ("rfq confirmed", "RFQ Confirmed"),
                ("sent", "RFQ Sent"),
                ("to approve", "To Approve"),
                ("approved", "Approved"),
                ("purchase", "Purchase Order"),
                ("done", "Locked"),
                ("cancel", "Cancelled"),
            ],
        )
