# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# flake8: noqa: C901

from sqlalchemy import text as sql_text

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class WizardSyncStockWhsMssql(models.TransientModel):
    _name = "wizard.sync.stock.whs.mssql"
    _description = "Synchronize stock inventory with Remote Mssql DB"

    do_sync = fields.Boolean(string="Synchronize stock inventory")
    product_id = fields.Many2one("product.product", string="Product to sync")

    def apply(self):
        weight = False
        inventory = False
        inventory_lines_data = []
        inventory_obj = self.env["stock.inventory"]
        for wizard in self:
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
            # get and aggregate stock data from whs
            while True:
                giacenze_query = (
                    "SELECT * FROM (SELECT row_number() OVER (ORDER BY Articolo) "
                    "AS rownum, Articolo, Lotto, Lotto2, Lotto3, Lotto4, Lotto5, "
                    "dataora, Qta, Peso FROM HOST_GIACENZE) as A "
                    "WHERE A.rownum BETWEEN %s AND %s" % (i, i + 2000)
                )
                if wizard.product_id:
                    giacenze_query = giacenze_query.replace(
                        "HOST_GIACENZE",
                        "HOST_GIACENZE WHERE Articolo = '%s'"
                        % wizard.product_id.default_code,
                    )
                i += 2000
                esiti_liste = dbsource.execute_mssql(
                    sqlquery=sql_text(giacenze_query), sqlparams=None, metadata=None
                )
                # esiti_liste[0] contain result
                if not esiti_liste[0]:
                    break
                for esito_lista in esiti_liste[0]:
                    articolo = esito_lista[1]
                    # dataora = esito_lista[7]
                    try:
                        qty = float(esito_lista[8])
                    except ValueError:
                        qty = False
                    except TypeError:
                        qty = False
                    try:
                        weight = float(esito_lista[9]) / 1000.0
                    except ValueError:
                        weight = False
                    except TypeError:
                        weight = False
                    lot_unique_ref = " ".join(
                        [
                            esito_lista[k + 2].strip() if esito_lista[k + 2] else ""
                            for k, x in enumerate(esito_lista)
                            if k < 5
                        ]
                    )[:20]
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
                    ]
                )
                # if it is a service, only log but do not create inventory line
                if not product:
                    product = product_obj.search(
                        [
                            ("default_code", "=", stock_product),
                            ("type", "=", "service"),
                            ("exclude_from_whs", "!=", True),
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
                    open_whs_list_ids = self.env["hyddemo.whs.liste"].search([
                        ("product_id", "=", product.id),
                        ("stato", "=", "4"),
                        ("move_id.state", "!=", "done"),
                    ])
                    if open_whs_list_ids:
                        product_qty -= sum(open_whs_list_ids.mapped("qtamov"))
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
                                    "reason": "WHS synchronize",
                                }
                            )
                    else:
                        whs_log_line.update(
                            {
                                "product_id": product.id,
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
                    if weight:
                        weight = stock_product_dict[stock_product]["weight"]
                        uom_kgm = self.env.ref("uom.product_uom_kgm")
                        if product.weight_uom_id != uom_kgm:
                            if product.weight_uom_id.category_id == self.env.ref(
                                "uom.product_uom_categ_kgm"
                            ):
                                weight = uom_kgm._compute_quantity(
                                    weight, product.weight_uom_id
                                )
                            else:
                                whs_log_line.update(
                                    {
                                        "product_id": product.id,
                                        "weight": weight,
                                        "weight_wrong": product.weight,
                                        "type": "mismatch",
                                    }
                                )
                        if float_compare(
                            product.weight,
                            weight,
                            precision_rounding=product.weight_uom_id.rounding,
                        ):
                            whs_log_line.update(
                                {
                                    "product_id": product.id,
                                    "weight": weight,
                                    "weight_wrong": product.weight,
                                    "type": "mismatch",
                                }
                            )
                            if wizard.do_sync:
                                product.write(
                                    {
                                        "weight": weight,
                                    }
                                )
                if whs_log_line.get("type"):
                    whs_log_lines.append(whs_log_line)

            if wizard.do_sync and inventory_lines_data:
                inventory = inventory_obj.create(
                    {
                        "name": "WHS sync inventory "
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
                        "inventory_id": inventory.id if inventory else False,
                        "hyddemo_mssql_log_line_ids": [
                            (0, 0, x) for x in whs_log_lines
                        ],
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
