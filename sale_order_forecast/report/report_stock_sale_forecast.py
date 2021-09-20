# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import tools
from odoo import api, fields, models, _


class ReportStockSaleForecast(models.Model):
    # la query deve restituire le qtà disponibili quando variate per data in base
    # ai seguenti oggetti:
    # stock.quant - stock.move: riutilizzare la ricerca di report.stock.forecast
    # che restituisce le quantità in ingresso/uscita per data
    # sale.order.line con lo stato 'bozza' o 'inviato', in quanto i confermati sono
    # già presenti, e in cui sia impostato il campo commitment date nell'so o sol
    # purchase.order con lo stato confermato sono già presenti nelle stock.move
    # stock.move per le righe di produzione non eseguite

    # Prodotto 	    Tipo di prodotto 	            Percorsi
    # [PP0268]      tubo aspirazione 3/8 BSP 68mm 	Prodotto Stoccabile Acquista

    # Required in this order 	Quantity On Hand 	Quantity in sales quotations
    # 1                      	4.658,000           1,00

    # available - outgoing in orders	            Stock at end of period
    #  and quotations                               with quotations
    # 4.517 	                                    4.657,00

    # Data disponibilità	Status Regarding  	Giorni 	Giorni 	    Giorni
    #  prevista             Quotations          totali  Produzione  di spedizione
    #                       Available for  	    0 	    0 	        0
    #                       all orders
    # TODO verificare se i dati in 'C - Manufacture' sono già estratti dallo stock
    #  in teoria questi dati sono la parte di produzione non prodotta
    #  e la parte di consumi non fatta

    _name = 'report.stock.sale.forecast'
    _auto = False
    _description = 'Stock Sale Forecast Report'
    _rec_name = 'date'
    _order = 'date desc'

    @api.model
    def _get_done_states(self):
        return ['sale', 'done', 'paid']

    name = fields.Char('Order Reference', readonly=True)
    date = fields.Date('Date', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    product_tmpl_id = fields.Many2one(
        'product.template', string='Product Template',
        related='product_id.product_tmpl_id', readonly=True)
    child_product_id = fields.Many2one(
        'product.product', 'Child product', readonly=True)
    quantity = fields.Float(readonly=True)
    cumulative_quantity = fields.Float(readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    order_id = fields.Many2one('sale.order', 'Order #', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
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
        """

        union_select_ = """
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
            CASE WHEN MAIN.date = SUB.date THEN sum(MAIN.product_qty) ELSE 0 END as product_qty,
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
            WHERE product_qty != 0
            GROUP BY product_id,date,company_id

            UNION (
            WITH RECURSIVE bom_products AS (
                SELECT
                    sol.product_id as root_product_id,
                    mbl.product_id,
                    mbl.product_qty,
                    sol.order_id,
                    sol.product_uom_qty,
                    so.state,
                    CASE WHEN sol.commitment_date IS NOT NULL
                    THEN to_char(sol.commitment_date, 'YYYY-MM-DD')
                    ELSE to_char(so.commitment_date, 'YYYY-MM-DD') END
                    AS date,
                    so.company_id
                FROM
                    mrp_bom_line mbl
                LEFT JOIN mrp_bom mb ON mb.id = mbl.bom_id
                LEFT JOIN sale_order_line sol ON sol.product_id = mb.product_id
                LEFT JOIN sale_order so ON so.id = sol.order_id
                WHERE
                    mb.product_id IS NOT NULL
                    AND so.state in ('draft', 'sent')
                    AND (sol.commitment_date IS NOT NULL 
                         OR so.commitment_date IS NOT NULL)
                UNION
                    SELECT
                        bp.product_id as root_product_id,
                        mbl1.product_id,
                        mbl1.product_qty,
                        bp.order_id,
                        bp.product_uom_qty,
                        bp.state,
                        bp.date,
                        bp.company_id
                    FROM
                        mrp_bom_line mbl1
                    LEFT JOIN mrp_bom mb1 on mb1.id = mbl1.bom_id
                    INNER JOIN bom_products bp ON bp.product_id = mb1.product_id
                    WHERE
                        bp.state in ('draft', 'sent')
                        AND bp.date IS NOT NULL
            ) SELECT
                row_number() OVER () AS id,
                order_id AS order_id,
                'D - Bom component' AS name,
                root_product_id AS product_id,
                product_id AS child_product_id,
                date AS date,
                -product_qty * product_uom_qty AS quantity,
                company_id AS company_id
            FROM
                bom_products WHERE product_qty != 0 ORDER BY product_id
            )

            UNION
            SELECT
            MIN(smp.id) AS id,
            NULL AS order_id,
            'C - Manufacture' AS name,
            smp.product_id AS product_id,
            smp.product_id AS child_product_id,
            to_char(smp.date_expected, 'YYYY-MM-DD') AS date,
            sum(-smp.product_qty) AS quantity,
            smp.company_id
            FROM stock_move smp
            LEFT JOIN mrp_production mp ON mp.id = smp.raw_material_production_id
            WHERE smp.raw_material_production_id IS NOT NULL
            AND smp.state not in ('done', 'cancel')
            GROUP BY
            smp.product_id,
            smp.date_expected,
            smp.date,
            smp.company_id

            UNION
            SELECT
            MIN(mp1.id) AS id,
            NULL AS order_id,
            'C - Manufacture' AS name,
            mp1.product_id AS product_id,
            mp1.product_id AS child_product_id,
            to_char(mp1.date_planned_start, 'YYYY-MM-DD') AS date,
            sum(mp1.product_qty) +sum(-smlp.product_qty) AS quantity,
            mp1.company_id
            FROM mrp_production mp1
            LEFT JOIN stock_move smpp ON smpp.production_id = mp1.id
            LEFT JOIN stock_move_line smlp ON smlp.move_id = smpp.id
            WHERE mp1.state not in ('done', 'cancel')
            GROUP BY
            mp1.product_id,
            date_planned_start,
            mp1.company_id
        """

        for field in fields.values():
            select_ += field

        from_ = """
            sale_order_line l
                  join sale_order s on (l.order_id=s.id)
                  join res_partner partner on s.partner_id = partner.id
                    left join product_product p on (l.product_id=p.id)
                        left join product_template t on (p.product_tmpl_id=t.id)
                left join uom_uom u on (u.id=l.product_uom)
                left join uom_uom u2 on (u2.id=t.uom_id)
            %s
        """ % from_clause

        groupby_ = """
            l.product_id,
            l.order_id,
            t.uom_id,
            l.commitment_date,
            s.company_id,
            s.id %s
        """ % groupby

        res = """
            %s (SELECT
            MIN(sub.id) AS id,
            sub.order_id AS order_id,
            MIN(sub.name) AS name,
            sub.product_id AS product_id,
            sub.child_product_id AS child_product_id,
            sub.date AS date,
            SUM(sub.quantity) AS quantity,
            CASE WHEN MIN(sub.name) = 'B - Stock'
            THEN
            SUM(SUM(sub.quantity))
            OVER (PARTITION BY sub.child_product_id ORDER BY sub.date)
            ELSE NULL
            END
            AS cumulative_quantity,
            MIN(sub.company_id) AS company_id
            FROM (SELECT %s FROM %s WHERE s.state IN ('draft', 'sent')
            AND s.active = 't'
            AND (s.commitment_date IS NOT NULL OR l.commitment_date IS NOT NULL)
            AND l.product_id IS NOT NULL
            GROUP BY %s %s) AS sub
            GROUP BY product_id, child_product_id, date, order_id)
            """ % (
                with_, select_, from_, groupby_, union_select_)
        return res

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (
            self._table, self._query()))

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None,
                   orderby=False, lazy=True):
        """Remove qtys in groupby for product_id as it is only used as header.
        """
        res = super(ReportStockSaleForecast, self).read_group(
            domain, fields, groupby, offset=offset, limit=limit,
            orderby=orderby, lazy=lazy,
        )
        if 'product_id' in groupby and 'child_product_id' not in groupby:
            for line in res:
                del line['quantity']
                del line['cumulative_quantity']
            return res
        return res
