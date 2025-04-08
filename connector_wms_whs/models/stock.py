from odoo import models, fields

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
            whsliste_data["priorita"] = max(
                [int(move.sale_line_id.priority), 0]
            )
        elif move.priority:
            whsliste_data["priorita"] = max([int(move.priority), 0])
        return whsliste_data


class Picking(models.Model):
    _inherit = "stock.picking"

    priority = fields.Selection(
        selection_add=[("2", "Very Urgent")],
        ondelete={"2": lambda r: r.write({"priority": "1"})},
    )
