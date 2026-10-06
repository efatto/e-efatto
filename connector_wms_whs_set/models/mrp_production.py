import logging

from odoo import _, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _get_tipo(self, is_custom=False):
        res = super()._get_tipo(is_custom=is_custom)
        if self.production_left_set_ids or self.production_right_set_ids:
            res = "12"
        return res

    def _get_num_lista(self):
        production_set_ids = (
            self.production_left_set_ids | self.production_right_set_ids
        )
        if production_set_ids:
            production_set_ids.ensure_one()
            num_lista = (
                production_set_ids.production_left_id
                | production_set_ids.production_right_id
            ).mapped("move_raw_ids.whs_list_ids").filtered(
                lambda whsl: whsl.stato != "3"
            ).mapped("num_lista")[:1]
            if num_lista:
                num_lista = num_lista[0]
            else:
                num_lista, _riga = super()._get_num_lista()
            riga = 0 if self.production_left_set_ids else 1
            # get num_lista from the first whs_list_ids as they must be the same
            # (there could be more than one whs_list_ids if the production is split)
            return num_lista, riga
        return super()._get_num_lista()

    def _create_whs_list_raw_move(
        self, move, num_lista, is_custom, riga=0, qty_producing=0
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
        res = super()._create_whs_list_raw_move(
            move, num_lista, is_custom, riga, qty_producing=qty_producing
        )
        for riga_number, attr_name in [
            (1, "production_left_set_ids"),
            (2, "production_right_set_ids"),
        ]:
            if getattr(self, attr_name):
                if not getattr(self, attr_name).split_production:
                    new_riga_number = self.move_raw_ids.mapped("whs_list_ids.riga")
                    if new_riga_number and new_riga_number[0] != riga_number:
                        raise ValidationError(
                            _(
                                "In %(attr_name)s production whs list riga must be "
                                "%(riga_number)s, but is %(new_riga_number)s",
                                attr_name=attr_name,
                                riga_number=riga_number,
                                new_riga_number=new_riga_number,
                            )
                        )
                else:
                    new_riga_numbers = set(self.move_raw_ids.mapped("whs_list_ids.riga")) - {1, 2}
                    if new_riga_numbers:
                        raise ValidationError(
                            _(
                                "Only 1 and 2 are valid number in whs list riga linked "
                                "to a production set, but are %(new_riga_numbers)s",
                                new_riga_numbers=new_riga_numbers,
                            )
                        )
        return res
