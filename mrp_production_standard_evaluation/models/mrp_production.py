from odoo import models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    # TODO i costi dei prodotti consumati vanno aggiornati quando si completa la
    #  produzione con i costi standard in quel momento. Il costo dei prodotti finiti
    #  saranno di conseguenza. Poi vanno aggiornati se ci sono modifiche ai consumati
    #  nelle quantità o nei costi. Poi vanno aggiornati anche se ci sono modifiche ai
    #  tempi di lavorazione o ai costi dei centri di lavoro. Infine va aggiornato
    #  il costo di questo componente se fa parte di eventuali produzioni da cui questa
    #  produzione ha avuto origine. OPPURE usando il campo is_locked
    # todo eseguire _cal_price per far ricalcolare il costo totale dei finiti
    #  questo metodo viene chiamato da _post_inventory() con la lista dei consumati
    #  che viene chiamato a sua volta da button_mark_done(), quindi va aggiunta una
    #  chiamata direi dal write() su stock.move intercettando qualsiasi modifica
    #  sulle quantità consumate o sui price_unit

    def _cal_price(self, consumed_moves):
        """Set a price unit on the finished move according to `consumed_moves`.
        Original method has been overwritten to set costs of finished products to the
        registered costs on stock moves, using the price unit set on creation, instead
        of the stock_valuation_layer, which is a fiscal value, not the best for an internal evaluation.
        TODO: update the price unit of stock moves when moved?
        """
        res = super()._cal_price(consumed_moves)
        work_center_cost = 0
        finished_move = self.move_finished_ids.filtered(
            lambda x: x.product_id == self.product_id
            and x.state not in ("done", "cancel")
            and x.quantity_done > 0
        )
        if finished_move:
            finished_move.ensure_one()
            for work_order in self.workorder_ids:
                time_lines = work_order.time_ids.filtered(
                    lambda x: x.date_end and not x.cost_already_recorded
                )
                duration = sum(time_lines.mapped("duration"))
                time_lines.write({"cost_already_recorded": True})
                work_center_cost += (
                    duration / 60.0
                ) * work_order.workcenter_id.costs_hour
            if finished_move.product_id.cost_method not in ("fifo", "average"):
                qty_done = finished_move.product_uom._compute_quantity(
                    finished_move.quantity_done, finished_move.product_id.uom_id
                )
                # get actual cost from consumed_moves
                extra_cost = self.extra_cost * qty_done
                finished_move.price_unit = (
                    sum(
                        move.quantity_done * move.price_unit
                        for move in consumed_moves.sudo())
                    + work_center_cost
                    + extra_cost
                ) / qty_done
        return res

    # def _costs_generate(self):
    #     """ Calculates total costs at the end of the production.
    #     """
    #     self.ensure_one()
    #     AccountAnalyticLine = self.env['account.analytic.line'].sudo()
    #     for wc_line in self.workorder_ids.filtered(
    #       'workcenter_id.costs_hour_account_id'):
    #         vals = self._prepare_wc_analytic_line(wc_line)
    #         precision_rounding = (
    #           wc_line.workcenter_id.costs_hour_account_id.currency_id
    #           or self.company_id.currency_id).rounding
    #         if not float_is_zero(
    #           vals.get('amount', 0.0), precision_rounding=precision_rounding):
    #             # we use SUPERUSER_ID as we do not guarantee an mrp user
    #             # has access to account analytic lines but still should be
    #             # able to produce orders
    #             AccountAnalyticLine.create(vals)
