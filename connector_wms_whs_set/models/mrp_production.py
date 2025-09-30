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
            if left.move_raw_ids.whs_list_ids:
                num_lista = left.move_raw_ids.whs_list_ids.num_lista
                riga = 1
            elif right.move_raw_ids.whs_list_ids:
                num_lista = right.move_raw_ids.whs_list_ids.num_lista
                riga = 1
        if not num_lista:
            num_lista, riga = super()._get_num_lista()
        return num_lista, riga
