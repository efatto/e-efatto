# Copyright 2020 Tecnativa - Ernesto Tejeda
# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from collections import defaultdict
from datetime import timedelta

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    virtual_available_at_date = fields.Float(
        compute='_compute_stock_qty_at_date', store=True)
    scheduled_date = fields.Datetime(
        compute='_compute_stock_qty_at_date', store=True)
    free_qty_today = fields.Float(
        compute='_compute_stock_qty_at_date', store=True)
    qty_available_today = fields.Float(
        compute='_compute_stock_qty_at_date', store=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse', compute='_compute_stock_qty_at_date', store=True)
    qty_to_deliver = fields.Float(store=True)
    is_mto = fields.Boolean(store=True)
    display_qty_widget = fields.Boolean(store=True)

    @api.depends('product_id', 'product_uom_qty', 'qty_delivered', 'state',
                 'commitment_date', 'order_id.commitment_date')
    def _compute_qty_to_deliver(self):
        """ Based on _compute_qty_to_deliver method of sale.order.line
            model in Odoo v13 'sale_stock' module.
        """
        for line in self:
            line.qty_to_deliver = line.product_uom_qty - line.qty_delivered
            line.display_qty_widget = (line.state == 'draft'
                                       and not line.commitment_date
                                       and not line.order_id.commitment_date
                                       and line.product_type == 'product'
                                       and line.qty_to_deliver > 0)

    @api.depends('product_id', 'product_uom_qty', 'commitment_date')
    def _compute_stock_qty_at_date(self):
        """ Based on _compute_free_qty method of sale.order.line
            model in Odoo v13 'sale_stock' module.
        """
        #  we expose the first date in which the products are really
        #  available from stock to customer
        # do not do super() as this override other logic and consume time
        # storing fields will not recall this method on all record at every change
        # consider previsional consumed components
        # do not consider manufacturing products
        qty_processed_per_product = defaultdict(lambda: 0)
        for line in self.sorted(key=lambda r: r.sequence):
            if not line.product_id:
                continue
            line.warehouse_id = line.order_id.warehouse_id
            self._cr.execute("""
            SELECT
                sub.date,
                sub.product_id,
                sub.child_product_id,
                SUM(sub.quantity) AS quantity,
                SUM(SUM(sub.quantity))
                OVER (PARTITION BY sub.child_product_id ORDER BY sub.date)
                AS cumulative_quantity
            FROM
            (
            SELECT
                min(l.id) AS id,
                s.id AS order_id,
                'A - Sale' AS name,
                l.product_id AS product_id,
                l.product_id AS child_product_id,
                CASE WHEN l.commitment_date IS NOT NULL
                THEN to_char(l.commitment_date, 'YYYY-MM-DD')
                ELSE to_char(s.commitment_date, 'YYYY-MM-DD') END
                AS date,
                sum(l.product_uom_qty / u.factor * u2.factor) * -1 as quantity,
                s.company_id as company_id
            FROM
                sale_order_line l
                  join sale_order s on (l.order_id=s.id)
                  join res_partner partner on s.partner_id = partner.id
                    left join product_product p on (l.product_id=p.id)
                        left join product_template t on (p.product_tmpl_id=t.id)
                left join uom_uom u on (u.id=l.product_uom)
                left join uom_uom u2 on (u2.id=t.uom_id)
            WHERE
                s.state IN ('draft', 'sent')
                AND s.active = 't'
                AND (s.commitment_date IS NOT NULL OR l.commitment_date IS NOT NULL)
                AND l.product_id = %s
            GROUP BY
                l.product_id,
                l.order_id,
                t.uom_id,
                l.commitment_date,
                s.company_id,
                s.id
            UNION SELECT
                MIN(id) as id,
                null as order_id,
                'B - Stock' AS name,
                product_id as product_id,
                product_id as child_product_id,
                to_char(date, 'YYYY-MM-DD') as date,
                sum(product_qty) AS quantity,
                company_id
            FROM 
                (SELECT
                MIN(id) as id,
                MAIN.product_id as product_id,
                SUB.date as date,
                CASE WHEN MAIN.date = SUB.date 
                    THEN sum(MAIN.product_qty) ELSE 0 END as product_qty,
                MAIN.company_id as company_id
                FROM
                    (SELECT
                        MIN(sq.id) as id,
                        sq.product_id,
                        CURRENT_DATE as date,
                        SUM(sq.quantity) AS product_qty,
                        sq.company_id
                        FROM
                        stock_quant as sq
                        LEFT JOIN
                        product_product ON product_product.id = sq.product_id
                        LEFT JOIN
                        stock_location location_id ON sq.location_id = location_id.id
                        WHERE
                        location_id.usage = 'internal'
                        GROUP BY date, sq.product_id, sq.company_id
                        UNION ALL
                        SELECT
                        MIN(-sm.id) as id,
                        sm.product_id,
                        CASE WHEN sm.date_expected > CURRENT_DATE
                        THEN sm.date_expected
                        ELSE CURRENT_DATE END
                        AS date,
                        SUM(sm.product_qty) AS product_qty,
                        sm.company_id
                        FROM
                           stock_move as sm
                        LEFT JOIN
                           product_product ON product_product.id = sm.product_id
                        LEFT JOIN
                        stock_location dest_location ON sm.location_dest_id = dest_location.id
                        LEFT JOIN
                        stock_location source_location ON sm.location_id = source_location.id
                        WHERE
                        sm.state IN ('confirmed','partially_available','assigned','waiting') and
                        source_location.usage != 'internal' and dest_location.usage = 'internal'
                        GROUP BY sm.date_expected, sm.product_id, sm.company_id
                        UNION ALL
                        SELECT
                            MIN(-sm.id) as id,
                            sm.product_id,
                            CASE WHEN sm.date_expected > CURRENT_DATE
                                THEN sm.date_expected
                                ELSE CURRENT_DATE END
                            AS date,
                            SUM(-(sm.product_qty)) AS product_qty,
                            sm.company_id
                        FROM
                           stock_move as sm
                        LEFT JOIN
                           product_product ON product_product.id = sm.product_id
                        LEFT JOIN
                           stock_location source_location ON sm.location_id = source_location.id
                        LEFT JOIN
                           stock_location dest_location ON sm.location_dest_id = dest_location.id
                        WHERE
                            sm.state IN ('confirmed','partially_available','assigned','waiting') and
                        source_location.usage = 'internal' and dest_location.usage != 'internal'
                        GROUP BY sm.date_expected,sm.product_id, sm.company_id)
                     as MAIN
                     LEFT JOIN
                     (SELECT DISTINCT date
                      FROM
                      (
                         SELECT CURRENT_DATE AS DATE
                         UNION ALL
                         SELECT sm.date_expected AS date
                         FROM stock_move sm
                         LEFT JOIN
                         stock_location source_location ON sm.location_id = source_location.id
                         LEFT JOIN
                         stock_location dest_location ON sm.location_dest_id = dest_location.id
                         WHERE
                         sm.state IN ('confirmed','assigned','waiting')
                         and sm.date_expected > CURRENT_DATE
                         and ((dest_location.usage = 'internal' 
                         AND source_location.usage != 'internal')
                          or (source_location.usage = 'internal' 
                         AND dest_location.usage != 'internal'))) AS DATE_SEARCH)
                         SUB ON (SUB.date IS NOT NULL)
                    GROUP BY MAIN.product_id,SUB.date, MAIN.date, MAIN.company_id
                    ) AS FINAL
                WHERE product_qty != 0 AND product_id = %s
                GROUP BY product_id, date, company_id
                ) AS sub
                GROUP BY product_id, child_product_id, date
            """, (line.product_id.id, line.product_id.id,))
            res = self._cr.dictfetchall()
            # dates on which availability is enough for requested qty
            candidate_availables = [
                x for x in res if x['cumulative_quantity'] >= line.product_uom_qty]
            # se ci sono date successive con quantità negativa, non è disponibile
            availables = []
            for candidate_available in candidate_availables:
                not_available = [
                    x for x in res if
                    x['cumulative_quantity'] < line.product_uom_qty
                    and x['date'] >= candidate_available['date']
                ]
                if not_available:
                    continue
                availables.append(candidate_available)
            lower_available_qty = 0
            if availables:
                # check if this move, available in a certain date, will remove product
                # reserved for future, so stock will become negative
                lower_available_qty = availables[0]['cumulative_quantity']
                for available in availables:
                    if available['cumulative_quantity'] < lower_available_qty:
                        lower_available_qty = available['cumulative_quantity']
                if lower_available_qty < line.product_uom_qty:
                    availables = []
            if availables:
                # there are multiple available dates: get the lower qty
                availables.sort(key=lambda self: self['cumulative_quantity'])
                available = availables[0]
                # show the first available date
                availables.sort(key=lambda self: self['date'])
                available_date = availables[0]
                scheduled_date = fields.Datetime.from_string(available_date['date'])
                # product = line.product_id.with_context(
                #     to_date=scheduled_date, warehouse=line.warehouse_id.id)
                # qty_available = available['cumulative_quantity']
                # free_qty = product.free_qty
                # show the lower quantity available
                virtual_available = available['cumulative_quantity']
                qty_processed = qty_processed_per_product[line.product_id.id]
                line.scheduled_date = scheduled_date
                line.qty_available_today = 0
                line.free_qty_today = available['cumulative_quantity']
                virtual_available_at_date = virtual_available - qty_processed
                line.virtual_available_at_date = virtual_available_at_date
                qty_processed_per_product[line.product_id.id] += line.product_uom_qty
            else:
                line.virtual_available_at_date = lower_available_qty
                line.scheduled_date = line.commitment_date\
                    and line.commitment_date + timedelta(days=1)\
                    or fields.Datetime.now()
                line.free_qty_today = 0
                line.qty_available_today = 0
