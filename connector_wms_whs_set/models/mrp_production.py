import logging

from odoo import models

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _get_tipo(self, is_custom=False):
        res = super()._get_tipo(is_custom=is_custom)
        if self.production_left_set_ids or self.production_right_set_ids:
            res = "12"
        return res

    def _get_num_lista(self):
        num_lista = False
        riga = 0
        production_set_ids = (
            self.production_left_set_ids | self.production_right_set_ids
        )
        if production_set_ids:
            production_set_ids.ensure_one()
            left = production_set_ids.production_left_id
            right = production_set_ids.production_right_id
            # get num_lista from the first whs_list_ids as they must be the same
            # (there could be more than one whs_list_ids if the production is split)
            if left.move_raw_ids.whs_list_ids:
                num_lista = left.move_raw_ids.whs_list_ids[0].num_lista
                riga = 1
            elif right.move_raw_ids.whs_list_ids:
                num_lista = right.move_raw_ids.whs_list_ids[0].num_lista
                riga = 2
        if not num_lista:
            num_lista, riga = super()._get_num_lista()
        return num_lista, riga

    def _create_whs_list_raw_move(
        self, move, num_lista, riga, is_custom, qty_producing=0
    ):
        if (
            self.production_left_set_ids | self.production_right_set_ids
        ).split_production:
            qty_producing = (
                self.production_left_set_ids
                and not self.production_left_set_ids.sent_to_whs
                and self.production_left_set_ids.qty_producing_left
                or self.production_right_set_ids.qty_producing_right
            )
        return super()._create_whs_list_raw_move(
            move, num_lista, riga, is_custom, qty_producing=qty_producing
        )
