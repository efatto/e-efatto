from odoo import fields, models

# priority (priorità) da odoo14 i valori corrispondono (0='0', ecc.)
# odoo14: [('0', 'Normal'), ('1', 'Urgent')]
# odoo12: [('0', 'Not urgent'), ('1', 'Normal'), ('2', 'Urgent'), ('3', 'Very Urgent')]
# lo script di migrazione attuale traduce '1' a '0' (giusto), '2' a '1' (giusto) e
# '3' a '1' (sbagliato): todo correggere che '3' diventi '2', magari su un banale sql
# whs: # 0=Bassa; 1=Media; 2=Urgente


class StockMove(models.Model):
    _inherit = "stock.move"

    priority = fields.Selection(
        selection_add=[("2", "Very Urgent")],
        ondelete={"2": lambda r: r.write({"priority": "1"})},
    )

    @staticmethod
    def _set_priority(move, whsliste_data):
        if move.sale_line_id.priority:
            whsliste_data["priorita"] = max([int(move.sale_line_id.priority), 0])
        elif move.priority:
            whsliste_data["priorita"] = max([int(move.priority), 0])
        return whsliste_data

    def custom_check_mrp(self):
        # Do not create WMS lists for finished products that have an MTO route
        # and with category name equal to CUSTOM
        self.ensure_one()
        if all(
            [
                x
                in [
                    self.env.ref("mrp.route_warehouse0_manufacture"),
                    self.env.ref("stock.route_warehouse0_mto"),
                ]
                for x in self.product_id.route_ids
            ]
        ):
            # Never create whs list for OUT or IN related to
            # CUSTOM manufactured products, only create MO.
            # The IN will be without whs_list_ids so freely validatable
            # as production is done.
            # Same for the OUT, that one will be based only on Odoo
            # stock current availability (user has to check this one is
            # correct)
            if self.procure_method == "make_to_order":
                return True
        return False


class Picking(models.Model):
    _inherit = "stock.picking"

    priority = fields.Selection(
        selection_add=[("2", "Very Urgent")],
        ondelete={"2": lambda r: r.write({"priority": "1"})},
    )
