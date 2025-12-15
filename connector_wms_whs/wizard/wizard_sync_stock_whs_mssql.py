# flake8: noqa: C901
from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare

from odoo.addons.connector_whs.models.base_external_dbsource import clean_sql_text


class WizardSyncStockWhsMssql(models.TransientModel):
    _inherit = "wizard.sync.stock.whs.mssql"

    @staticmethod
    def _prepare_giacenze_query(i):
        # overridable method
        # respect order of fields retrieved!
        query = (
            "SELECT * FROM (SELECT row_number() OVER (ORDER BY Articolo) "
            "AS rownum, Articolo, Qta, Peso, "
            "Lotto, Lotto2, Lotto3, Lotto4, Lotto5 "
            "FROM HOST_GIACENZE) as A "
            "WHERE A.rownum BETWEEN %s AND %s" % (i, i + 2000)
        )
        return query

    def apply(self):
        fields_pos_dict = {
            "rownum": 0,
            "Articolo": 1,
            "Qta": 2,
            "Peso": 3,
            "Lotto": 4,
            "Lotto2": 5,
            "Lotto3": 6,
            "Lotto4": 7,
            "Lotto5": 8,
        }
        weight = 0
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
            raise UserError(_("Failed to open connection!"))
        new_last_update = fields.Datetime.now()
        product_obj = self.env["product.product"]
        i = 0
        whs_log_lines = []
        stock_product_dict = dict()
        # get and aggregate stock data from wms
        while True:
            giacenze_query = self._prepare_giacenze_query(i)
            if wizard.product_id:
                giacenze_query = giacenze_query.replace(
                    "HOST_GIACENZE",
                    "HOST_GIACENZE WHERE Articolo = '%s'"
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
                try:
                    weight = float(esito_lista[fields_pos_dict["Peso"]]) / 1000.0
                except ValueError:
                    weight = False
                except TypeError:
                    weight = False
                lot_unique_ref_list = []
                for key in fields_pos_dict.keys():
                    if "Lot" in key and esito_lista[fields_pos_dict[key]]:
                        lot_unique_ref_list.append(esito_lista[fields_pos_dict[key]])
                lot_unique_ref = " ".join(lot_unique_ref_list)[:20]
                if articolo not in stock_product_dict:
                    stock_product_dict.update(
                        {articolo: {lot_unique_ref: qty, "weight": weight}}
                    )
                else:
                    stock_product_dict[articolo].update({"weight": weight})
                    if lot_unique_ref not in stock_product_dict[articolo].keys():
                        stock_product_dict[articolo].update({lot_unique_ref: qty})
                    else:
                        stock_product_dict[articolo][lot_unique_ref] += qty

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
                            "lot": " ".join(
                                [
                                    x
                                    for x in stock_product_dict[stock_product]
                                    if x != "weight"
                                ]
                            ),
                        }
                    )
                    continue
                else:
                    whs_log_line.update(
                        {
                            "type": "service",
                            "lot": " ".join(
                                [
                                    x
                                    for x in stock_product_dict[stock_product]
                                    if x != "weight"
                                ]
                            ),
                        }
                    )
                    continue
            # it is a product or consumable, create log and align only if qty is
            # different and do_sync is True
            else:
                product_qty = sum(
                    [
                        stock_product_dict[stock_product][x]
                        for x in stock_product_dict[stock_product]
                        if x != "weight"
                    ]
                )
                # Remove from product_qty stock.move which whs lists
                # are on stato 'ricevuto esito' but not done in Odoo
                open_whs_list_ids = self.env["hyddemo.whs.liste"].search(
                    [
                        ("product_id", "=", product.id),
                        ("stato", "=", "4"),
                        ("move_id.state", "!=", "done"),
                    ]
                )
                if open_whs_list_ids:
                    # Neutralize the outgoing moves adding qty not completed in Odoo but
                    # completed in WHS, and viceversa for the incomings.
                    # Ignore MRP moves.
                    # `tipo`: "1"=out "2"=in "3"=inventory
                    # `tipo_mov`: mrpin mrpout move (unused: noback ripin ripout)
                    product_qty += sum(
                        [
                            x.qtamov * (1 if x.tipo[0] == "1" else -1)
                            for x in open_whs_list_ids
                            if "mrp" not in x.tipo_mov
                        ]
                    )
                # Remove (positive quantities) or add (negative quantities) availability
                # in the warehouse wh_qc_stock_loc_id (Quality control) location, which
                # is not available until the quality control ends.
                warehouse = dbsource.location_id.get_warehouse()
                wh_qc_qty = product.with_context(
                    location=warehouse.wh_qc_stock_loc_id.id
                ).qty_available
                product_qty += wh_qc_qty
                if product_qty < 0:
                    # do not consider negative quantities in WHS
                    whs_log_line.update(
                        {
                            "product_id": product.id,
                            "qty_wrong": product.qty_available,
                            "qty": product_qty,
                            "type": "mismatch",
                            "lot": " ".join(
                                [
                                    x
                                    for x in stock_product_dict[stock_product]
                                    if x != "weight"
                                ]
                            ),
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
                            "qty": product_qty,
                            "type": "mismatch",
                            "lot": " ".join(
                                [
                                    x
                                    for x in stock_product_dict[stock_product]
                                    if x != "weight"
                                ]
                            ),
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
                            "qty": product_qty,
                            "type": "ok",
                            "lot": " ".join(
                                [
                                    x
                                    for x in stock_product_dict[stock_product]
                                    if x != "weight"
                                ]
                            ),
                        }
                    )
                if stock_product_dict[stock_product].get("weight"):
                    product_weight = stock_product_dict[stock_product]["weight"]
                    uom_kgm = self.env.ref("uom.product_uom_kgm")
                    if product.weight_uom_id != uom_kgm:
                        if product.weight_uom_id.category_id == self.env.ref(
                            "uom.product_uom_categ_kgm"
                        ):
                            product_weight = uom_kgm._compute_quantity(
                                product_weight, product.weight_uom_id
                            )
                        else:
                            whs_log_line.update(
                                {
                                    "product_id": product.id,
                                    "qty_wrong": product.qty_available,
                                    "weight": product_weight,
                                    "weight_wrong": product.weight,
                                    "type": "mismatch",
                                }
                            )
                    if float_compare(
                        product.weight,
                        product_weight,
                        precision_rounding=product.weight_uom_id.rounding,
                    ):
                        whs_log_line.update(
                            {
                                "product_id": product.id,
                                "qty_wrong": product.qty_available,
                                "weight": product_weight,
                                "weight_wrong": product.weight,
                                "type": "mismatch",
                            }
                        )
                        if wizard.do_sync:
                            product.write(
                                {
                                    "weight": product_weight,
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
