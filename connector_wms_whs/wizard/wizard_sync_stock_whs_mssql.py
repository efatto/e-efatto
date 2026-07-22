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
            "SELECT * FROM (SELECT row_number() OVER (ORDER BY Articolo) "
            "AS rownum, Articolo, Qta, Peso, "
            "Lotto, Lotto2, Lotto3, Lotto4, Lotto5 "
            "FROM HOST_GIACENZE) as A "
            "WHERE A.rownum BETWEEN %s AND %s" % (i, i + 2000)
        )
        return query

    def apply(self):  # flake8: noqa: C901
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
            return None
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
                        {articolo: {lot_unique_ref: {"qty": qty, "weight": weight}}}
                    )
                else:
                    if lot_unique_ref not in stock_product_dict[articolo].keys():
                        stock_product_dict[articolo].update(
                            {lot_unique_ref: {"qty": qty, "weight": weight}}
                        )
                    else:
                        stock_product_dict[articolo][lot_unique_ref]["qty"] += qty

        # compare data with db and re-align values
        for stock_product in stock_product_dict:
            whs_log_line = {
                "name": stock_product,
            }
            product_lot = " ".join(stock_product_dict[stock_product].keys())
            product = product_obj.search(
                [
                    ("default_code", "=", stock_product),
                    ("type", "=", "product"),
                    ("exclude_from_whs", "!=", True),
                    ("is_kit", "!=", True),
                ]
            )
            # if it is a service, only log but do not create inventory line
            if not product:
                product = product_obj.search(
                    [
                        ("default_code", "=", stock_product),
                        ("type", "!=", "product"),
                        ("exclude_from_whs", "!=", True),
                        ("is_kit", "!=", True),
                    ]
                )
                if not product:
                    whs_log_line.update(
                        {
                            "type": "not_found",
                            "lot": product_lot,
                        }
                    )
                    continue
                else:
                    whs_log_line.update(
                        {
                            "type": "service",
                            "lot": product_lot,
                        }
                    )
                    continue
            # it is a product or consumable, create log and align only if qty is
            # different and do_sync is True
            else:
                wms_product_qty = sum(
                    [
                        stock_product_dict[stock_product][lot]["qty"]
                        for lot in stock_product_dict[stock_product]
                    ]
                )
                # Traceable products are not supported in this version
                if product.tracking != "none":
                    whs_log_line.update(
                        {
                            "type": "tracking",
                        }
                    )
                    continue
                # Remove from wms_product_qty stock.move which whs lists
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
                    wms_product_qty += ongoing_qty
                # Remove (positive quantities) or add (negative quantities) availability
                # in the warehouse wh_qc_stock_loc_id (Quality control) location, which
                # is not available until the quality control ends, from the qty got from
                # WMS.
                warehouse = dbsource.location_id.get_warehouse()
                wh_qc_qty = product.with_context(
                    location=warehouse.wh_qc_stock_loc_id.id
                ).qty_available
                wms_product_qty -= wh_qc_qty
                # Quality control location is a virtual location, so it is not computed
                # in this case.
                odoo_qty = product.with_context(
                    location=dbsource.location_id.id
                ).qty_available
                if wms_product_qty < 0:
                    # do not consider negative quantities in WHS
                    whs_log_line.update(
                        {
                            "product_id": product.id,
                            "qty_wrong": odoo_qty,
                            "ongoing_qty": ongoing_qty,
                            "qty": wms_product_qty,
                            "type": "mismatch",
                            "lot": product_lot,
                        }
                    )
                    continue
                if float_compare(
                    wms_product_qty,
                    odoo_qty,
                    precision_rounding=product.uom_id.rounding,
                ):
                    delta_qty = wms_product_qty - odoo_qty
                    whs_log_line.update(
                        {
                            "product_id": product.id,
                            "qty_wrong": odoo_qty,
                            "ongoing_qty": ongoing_qty,
                            "qty": wms_product_qty,
                            "type": "mismatch",
                            "lot": product_lot,
                        }
                    )
                    if wizard.do_sync:
                        # Distribute delta across locations:
                        # 1. Zero out negative child locations
                        # 2. Move positive qty to the main WMS loc if it's negative
                        # 3. Put the remaining diff in the main WMS loc
                        dbsource_loc = dbsource.location_id
                        qc_loc = (
                            warehouse.wh_qc_stock_loc_id
                            if warehouse
                            else self.env["stock.location"]
                        )
                        quant_groups = self.env["stock.quant"].read_group(
                            domain=[
                                ("product_id", "=", product.id),
                                (
                                    "location_id",
                                    "child_of",
                                    dbsource_loc.id,
                                ),
                            ],
                            fields=[
                                "location_id",
                                "quantity",
                            ],
                            groupby=["location_id"],
                        )
                        dbsource_loc_quant = [
                            x
                            for x in quant_groups
                            if x.get("location_id")[0] == dbsource_loc.id
                        ]
                        if dbsource_loc_quant:
                            base_loc_qty = dbsource_loc_quant[0]["quantity"]
                        else:
                            base_loc_qty = 0.0
                        neg_recovery = 0.0
                        pos_recovery = 0.0
                        for grp in quant_groups:
                            loc_id = grp["location_id"][0]
                            loc_qty = grp["quantity"]
                            if loc_id == dbsource_loc.id:
                                base_loc_qty = loc_qty
                                continue
                            # Skip QC location (anyway this is usually a virtual
                            # location, so this check should be skipped by default)
                            if qc_loc and loc_id == qc_loc.id:
                                continue
                            if loc_qty < 0 or loc_qty > 0 > base_loc_qty:
                                if loc_qty < 0:
                                    # Move from base location this qty to zero out
                                    # negative child
                                    neg_recovery += abs(loc_qty)
                                prod_qty = 0
                                if loc_qty > 0 > base_loc_qty:
                                    # Move to base location the possible qty to reduce
                                    # negative stock
                                    recovery = min([loc_qty, abs(base_loc_qty)])
                                    prod_qty = loc_qty - recovery
                                    pos_recovery += abs(recovery)
                                inventory_lines_data.append(
                                    {
                                        "product_qty": prod_qty,
                                        "location_id": loc_id,
                                        "product_id": product.id,
                                        "product_uom_id": product.uom_id.id,
                                        "reason": "WMS synchronize",
                                    }
                                )
                        # Add negative and positive children quantities to base location
                        base_new = (
                            base_loc_qty + delta_qty - neg_recovery + pos_recovery
                        )
                        if base_new < 0:
                            base_new = 0.0
                        inventory_lines_data.append(
                            {
                                "product_qty": base_new,
                                "location_id": dbsource_loc.id,
                                "product_id": product.id,
                                "product_uom_id": product.uom_id.id,
                                "reason": "WMS synchronize",
                            }
                        )
                else:
                    whs_log_line.update(
                        {
                            "product_id": product.id,
                            "qty_wrong": odoo_qty,
                            "ongoing_qty": ongoing_qty,
                            "qty": wms_product_qty,
                            "type": "ok",
                            "lot": product_lot,
                        }
                    )
                # get product weight from the lot with the highest qty
                wms_product_weight = 0.0
                product_lot_qty = 0.0
                for lot in stock_product_dict[stock_product]:
                    new_product_lot_qty = stock_product_dict[stock_product][lot]["qty"]
                    if new_product_lot_qty > product_lot_qty:
                        product_lot_qty = new_product_lot_qty
                        wms_product_weight = stock_product_dict[stock_product][lot][
                            "weight"
                        ]

                if wms_product_weight:
                    uom_kgm = self.env.ref("uom.product_uom_kgm")
                    if product.weight_uom_id != uom_kgm:
                        if product.weight_uom_id.category_id == self.env.ref(
                            "uom.product_uom_categ_kgm"
                        ):
                            wms_product_weight = uom_kgm._compute_quantity(
                                wms_product_weight, product.weight_uom_id
                            )
                    if float_compare(
                        product.weight,
                        wms_product_weight,
                        precision_rounding=product.weight_uom_id.rounding,
                    ):
                        whs_log_line.update(
                            {
                                "product_id": product.id,
                                "qty_wrong": odoo_qty,
                                "weight": wms_product_weight,
                                "weight_wrong": product.weight,
                                "type": "mismatch",
                            }
                        )
                        if wizard.do_sync:
                            product.write(
                                {
                                    "weight": wms_product_weight,
                                }
                            )
            if whs_log_line.get("type"):
                whs_log_lines.append(whs_log_line)

        if wizard.do_sync and inventory_lines_data:
            # Inventory get by default children locations
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
