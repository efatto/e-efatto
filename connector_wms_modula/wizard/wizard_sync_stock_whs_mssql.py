import logging

from odoo import fields, models
from odoo.tools import float_compare

from odoo.addons.connector_whs.models.base_external_dbsource import clean_sql_text

_logger = logging.getLogger(__name__)


class WizardSyncStockWhsMssql(models.TransientModel):
    _inherit = "wizard.sync.stock.whs.mssql"

    @staticmethod
    def _prepare_giacenze_query(i):
        # overridable method
        # respect order of fields retrieved!
        query = (
            "SELECT * FROM (SELECT row_number() OVER (ORDER BY GIA_ARTICOLO) "
            "AS rownum, GIA_ARTICOLO, GIA_GIAC, GIA_DATAORAS1 FROM EXP_GIACENZE) as A "
            "WHERE A.rownum BETWEEN %s AND %s AND A.GIA_DATAORAS1 = "
            "(SELECT MAX(GIA_DATAORAS1) FROM EXP_GIACENZE)" % (i, i + 2000)
        )
        return query

    def apply(self):  # noqa: C901
        fields_pos_dict = {
            "rownum": 0,
            "Articolo": 1,
            "Qta": 2,
            "DataOra": 3,
        }
        inventory_obj = self.env["stock.inventory"]
        inventory = inventory_obj.browse()
        inventory_lines_data = []
        self.ensure_one()
        wizard = self
        dbsource_obj = self.env["base.external.dbsource"]
        dbsource = dbsource_obj.browse(self._context["active_ids"])
        hyddemo_mssql_log_obj = self.env["hyddemo.mssql.log"]
        connection = dbsource.connection_open_mssql()
        if not connection:
            _logger.info("Failed to open connection!")
        new_last_update = fields.Datetime.now()
        product_obj = self.env["product.product"]
        i = 0
        whs_log_lines = []
        stock_product_dict = dict()
        # get and aggregate stock data from WMS
        while True:
            giacenze_query = self._prepare_giacenze_query(i)
            if wizard.product_id:
                giacenze_query = giacenze_query.replace(
                    "EXP_GIACENZE",
                    "EXP_GIACENZE WHERE GIA_ARTICOLO = '%s'"
                    % wizard.product_id.default_code,
                )
            i += 2000
            esiti_liste = dbsource.execute_mssql(
                sqlquery=clean_sql_text(giacenze_query),
                sqlparams=None,
                metadata=None,
            )
            # esiti_liste[0] contain result
            if not esiti_liste[0]:
                break
            for esito_lista in esiti_liste[0]:
                articolo = esito_lista[fields_pos_dict["Articolo"]]
                try:
                    qty = float(esito_lista[fields_pos_dict["Qta"]])
                except ValueError:
                    qty = False
                except TypeError:
                    qty = False
                if articolo not in stock_product_dict:
                    stock_product_dict.update({articolo: qty})
                else:
                    stock_product_dict[articolo] += qty

        # compare data with db and re-align values
        for stock_product in stock_product_dict:
            whs_log_line = {
                "name": stock_product,
            }
            product = product_obj.search(
                [
                    ("default_code", "=", stock_product),
                    ("type", "in", ["product", "consu"]),
                    ("exclude_from_whs", "!=", True),
                    ("is_kit", "!=", True),
                ]
            )
            # if it is a service, only log but do not create inventory line
            if not product:
                product = product_obj.search(
                    [
                        ("default_code", "=", stock_product),
                        ("type", "=", "service"),
                        ("exclude_from_whs", "!=", True),
                        ("is_kit", "!=", True),
                    ]
                )
                if not product:
                    whs_log_line.update(
                        {
                            "type": "not_found",
                        }
                    )
                    continue
                else:
                    whs_log_line.update(
                        {
                            "type": "service",
                        }
                    )
                    continue
            # it is a product or consumable, create log and align only if qty is
            # different and do_sync is True
            else:
                product_qty = stock_product_dict[stock_product]
                # it product is traceable, inventory cannot be done without lot info
                if product.tracking != "none":
                    whs_log_line.update(
                        {
                            "type": "tracking",
                        }
                    )
                    continue
                # Remove from product_qty stock.move which whs lists
                # are on stato 'ricevuto esito' but not done in Odoo
                ongoing_qty = 0
                open_whs_list_ids = self.env["hyddemo.whs.liste"].search(
                    [
                        ("product_id", "=", product.id),
                        ("stato", "=", "4"),
                        ("move_id.state", "not in", ["done", "cancel"]),
                    ]
                )
                if open_whs_list_ids:
                    # Neutralize the outgoing moves adding qty not completed in Odoo but
                    # completed in WHS, and viceversa for the incomings.
                    # Ignore MRP moves.
                    # `tipo`: "1"=out "2"=in "3"=inventory
                    # `tipo_mov`: mrpin mrpout move (unused: noback ripin ripout)
                    ongoing_qty = sum(
                        [
                            x.qtamov * (1 if x.tipo == "1" else -1)
                            for x in open_whs_list_ids
                            if "mrp" not in x.tipo_mov
                        ]
                    )
                    product_qty += ongoing_qty
                # Remove (positive quantities) or add (negative quantities) availability
                # in the warehouse wh_qc_stock_loc_id (Quality control) location, which
                # is not available until the quality control ends.
                warehouse = dbsource.location_id.get_warehouse()
                wh_qc_qty = product.with_context(
                    location=warehouse.wh_qc_stock_loc_id.id
                ).qty_available
                product_qty -= wh_qc_qty
                if product_qty < 0:
                    # do not consider negative quantities in WHS
                    whs_log_line.update(
                        {
                            "product_id": product.id,
                            "qty_wrong": product.qty_available,
                            "ongoing_qty": ongoing_qty,
                            "qty": product_qty,
                            "type": "mismatch",
                        }
                    )
                    continue
                if float_compare(
                    product_qty,
                    product.qty_available,
                    precision_rounding=product.uom_id.rounding,
                ):
                    whs_log_line.update(
                        {
                            "product_id": product.id,
                            "qty_wrong": product.qty_available,
                            "ongoing_qty": ongoing_qty,
                            "qty": product_qty,
                            "type": "mismatch",
                        }
                    )
                    if wizard.do_sync:
                        inventory_lines_data.append(
                            {
                                "product_qty": product_qty,
                                "location_id": dbsource.location_id.id,
                                "product_id": product.id,
                                "product_uom_id": product.uom_id.id,
                                "reason": "WMS synchronize",
                            }
                        )
                else:
                    whs_log_line.update(
                        {
                            "product_id": product.id,
                            "qty_wrong": product.qty_available,
                            "ongoing_qty": ongoing_qty,
                            "qty": product_qty,
                            "type": "ok",
                        }
                    )
            if whs_log_line.get("type"):
                whs_log_lines.append(whs_log_line)

        if wizard.do_sync and inventory_lines_data:
            inventory = inventory_obj.create(
                {
                    "name": "WMS sync inventory "
                    + new_last_update.strftime("%Y-%m-%d"),
                    "location_ids": [(6, 0, dbsource.location_id.ids)],
                    "company_id": dbsource.company_id.id,
                    "line_ids": [(0, 0, x) for x in inventory_lines_data],
                }
            )
            inventory.action_start()
            inventory.action_validate()

        hyddemo_mssql_log = hyddemo_mssql_log_obj.create(
            [
                {
                    "errori": "Stock inventory %s"
                    % ("sync" if wizard.do_sync else "check"),
                    "ultimo_invio": new_last_update,
                    "dbsource_id": dbsource.id,
                    "inventory_id": inventory.id,
                    "hyddemo_mssql_log_line_ids": [(0, 0, x) for x in whs_log_lines],
                }
            ]
        )

        return {
            "type": "ir.actions.act_window",
            "res_model": "hyddemo.mssql.log",
            "view_mode": "form",
            "view_type": "form",
            "res_id": hyddemo_mssql_log.id,
            "views": [(False, "form")],
            "target": "current",
        }
