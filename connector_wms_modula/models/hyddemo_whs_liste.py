import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.connector_whs.models.base_external_dbsource import clean_sql_text

_logger = logging.getLogger(__name__)

tipo_operazione_dict = {
    "1": "P",
    "2": "V",
    "3": "I",
    "4": "E",
}
LISTE_OPERATIONS = {
    "I": "Insert/Update",
    "D": "Delete",
    "A": "Add if row not exists",
    "H": "Add if header not exists",
    "Q": "Always add in queue",
    "R": "Replace",
}


class HyddemoWhsListe(models.Model):
    _inherit = "hyddemo.whs.liste"

    wms_modula_error = fields.Char(
        string="Error importing the list on WMS Modula",
    )
    wms_modula_riga_error = fields.Char(
        string="Error importing the row on WMS Modula",
    )

    def whs_unlink_lists(self, dbsource, db_type="IMP"):
        # do no call super() and put specific code
        for num_lista in set(self.mapped("num_lista")):
            current_whs_lists = self.filtered(lambda x: x.num_lista == num_lista)
            dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=clean_sql_text(
                    f"DELETE FROM {db_type}_ORDINI WHERE ORD_ORDINE=:ORD_ORDINE"
                ),
                sqlparams=dict(ORD_ORDINE=num_lista),
                metadata=None,
            )
            dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=clean_sql_text(
                    f"DELETE FROM {db_type}_ORDINI_RIGHE WHERE RIG_ORDINE=:RIG_ORDINE"
                ),
                sqlparams=dict(RIG_ORDINE=num_lista),
                metadata=None,
            )
            _logger.info("WMS LOG: unlink order and rows: %s" % num_lista)
            if db_type == "IMP":
                current_whs_lists.unlink()

    def whs_cancel_lists(self, dbsource):
        # do no call super() and put specific code
        # update lists to WMS, as they are possibly already elaborated from Modula user
        # sync EXP_ORDINI* tables, if they exist it means they are already processed by
        # Modula user
        # todo sincronizzare solo le tabelle EXP_*
        # check if the lists exist, to unlink or add an order to delete
        num_lista_list = set(self.mapped("num_lista"))
        todo_lists = self
        for num_lista in num_lista_list:
            to_cancel_lists = todo_lists.filtered(lambda x: x.num_lista == num_lista)
            todo_lists -= to_cancel_lists
            res = dbsource.execute_mssql(
                sqlquery=clean_sql_text(
                    "SELECT ORD_ORDINE FROM IMP_ORDINI WHERE ORD_OPERAZIONE='I' "
                    "AND ORD_ORDINE=:ORD_ORDINE"
                ),
                sqlparams=dict(ORD_ORDINE=num_lista),
                metadata=None,
            )
            if all(x.stato == "1" for x in to_cancel_lists):
                to_cancel_lists.whs_unlink_lists(dbsource)
            elif res and res[0]:
                # lista exists, so it's not elaborated from WMS, so unlink it directly
                # (this will unlink its rows too)
                to_cancel_lists.whs_unlink_lists(dbsource)
            else:
                # lista does not exist, so order to WMS to unlink it
                # (this will unlink its rows too)
                dbsource.with_context(no_return=True).execute_mssql(
                    sqlquery=clean_sql_text(
                        "INSERT INTO IMP_ORDINI (ORD_OPERAZIONE, ORD_ORDINE) VALUES "
                        "('D', :ORD_ORDINE)"
                    ),
                    sqlparams=dict(ORD_ORDINE=num_lista),
                    metadata=None,
                )
                _logger.info("WMS Modula LOG: delete Lista %s" % (num_lista))
                to_cancel_lists.write({"stato": "3"})

    @api.model
    def whs_check_lists(self, num_lista, dbsource):
        # do no call super() and put specific code
        elaborated_lists = dbsource.execute_mssql(
            sqlquery=clean_sql_text(
                "SELECT * FROM EXP_ORDINI_RIGHE WHERE RIG_ORDINE=:NUM_LISTA "
                "AND RIG_QTAE > 0"
            ),
            sqlparams=dict(NUM_LISTA=num_lista),
            metadata=None,
        )
        if elaborated_lists[0]:
            raise UserError(
                _(
                    "Trying to cancel lists elaborated from WMS, "
                    "please wait for cron synchronization or force it."
                )
            )
        deleting_lists = dbsource.execute_mssql(
            sqlquery=clean_sql_text(
                "SELECT * FROM IMP_ORDINI WHERE ORD_ORDINE=:NUM_LISTA "
                "AND ORD_OPERAZIONE='D'"
            ),
            sqlparams=dict(NUM_LISTA=num_lista),
            metadata=None,
        )
        if deleting_lists[0]:
            # todo delete records with 'D' operation?
            # hanno previsto che vada a cancellare io quei record? mi aspetterei che
            # Modula dopo aver eseguito l'operazione vada ad eliminarseli, che senso
            # ha che resti dentro?
            _logger.info(
                f"Deleted WMS list {num_lista} in Odoo already marked to be deleted "
                f"in WMS. Records with 'D' operation found: {str(deleting_lists[0])}"
            )

    def check_list_state(self):
        res = super().check_list_state()
        return res

    @staticmethod
    def _get_insert_order_line_query(params):
        insert_order_line_query = """
INSERT INTO IMP_ORDINI_RIGHE (
RIG_ORDINE,
RIG_HOSTINF,
RIG_ARTICOLO,
RIG_QTAR
)
VALUES (
:RIG_ORDINE,
:RIG_HOSTINF,
:RIG_ARTICOLO,
:RIG_QTAR
)
"""
        return insert_order_line_query.replace("\n", " ")

    @staticmethod
    def _get_insert_host_liste_query(params):
        insert_host_liste_query = """
INSERT INTO IMP_ORDINI (
ORD_OPERAZIONE,
ORD_ORDINE,
ORD_DES,
ORD_TIPOOP
)
VALUES (
:ORD_OPERAZIONE,
:ORD_ORDINE,
:ORD_DES,
:ORD_TIPOOP
)
"""
        return insert_host_liste_query.replace("\n", " ")

    def whs_prepare_host_liste_values(self):
        # do no call super() and put specific code
        execute_params_order = {}
        execute_params_order_line = {}
        for lista in self:
            if not execute_params_order.get(lista.num_lista):
                execute_params_order[lista.num_lista] = {
                    "ORD_OPERAZIONE": "I",
                    "ORD_ORDINE": lista.num_lista[:20],  # char 20
                    "ORD_DES": "%s - %s"
                    % (
                        lista.riferimento if lista.riferimento else "",
                        lista.ragsoc[
                            : 47 - (len(lista.riferimento) if lista.riferimento else 47)
                        ]
                        if lista.ragsoc
                        else "",
                    ),  # char 50
                    # 'ORD_PRIOHOST': lista.priorita,  # decimal(16,0) NOT IMPLEMENTED
                    "ORD_TIPOOP": tipo_operazione_dict[lista.tipo],  # char 5: P,V,I,E
                }
            product = lista.product_id
            if not execute_params_order_line.get(lista.num_lista):
                execute_params_order_line[lista.num_lista] = {}
            execute_params_order_line[lista.num_lista][lista.riga] = {
                "RIG_ORDINE": lista.num_lista[:20],  # char 20
                "RIG_HOSTINF": lista.riga,  # char 100
                "RIG_ARTICOLO": product.default_code[:50]
                if product.default_code
                else "prodotto %s senza codice" % product.id,  # char 50
                "RIG_QTAR": lista.qta,  # decimal(11,3)
            }
        return execute_params_order, execute_params_order_line
