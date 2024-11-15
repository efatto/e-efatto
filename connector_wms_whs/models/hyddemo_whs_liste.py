import logging

from odoo import api, models, _
from odoo.exceptions import UserError

from sqlalchemy import text as sql_text

_logger = logging.getLogger(__name__)


class HyddemoWhsListe(models.Model):
    _inherit = "hyddemo.whs.liste"

    def whs_unlink_lists(self, dbsource):
        # do no call super() and put specific code
        delete_lists_query = \
            "DELETE FROM HOST_LISTE WHERE NumLista = '%s' AND NumRiga = '%s'" % (
                self.num_lista,
                self.riga,
            )
        dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=sql_text(delete_lists_query.replace('\n', ' ')),
            sqlparams=None,
            metadata=None)
        _logger.info('WHS LOG: unlink Lista %s Riga %s' % (
            self.num_lista, self.riga
        ))
        self.unlink()

    def whs_cancel_lists(self, dbsource):
        # do no call super() and put specific code
        set_to_not_elaborate_query = \
            "UPDATE HOST_LISTE SET Elaborato=1, Qta=0 WHERE " \
            "NumLista='%s' AND NumRiga='%s'" % (self.num_lista, self.riga)
        dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=sql_text(set_to_not_elaborate_query), sqlparams=None,
            metadata=None)
        _logger.info('WHS LOG: cancel Lista %s Riga %s' % (
            self.num_lista, self.riga
        ))
        self.write({'stato': '3'})

    @api.model
    def whs_check_lists(self, num_lista, dbsource):
        # do no call super() and put specific code
        check_elaborated_lists_query = \
            "SELECT * FROM HOST_LISTE WHERE NumLista = '%s' " \
            "AND Elaborato = 4 AND QtaMovimentata > 0" % (
                num_lista,
            )
        elaborated_lists = dbsource.execute_mssql(
            sqlquery=sql_text(check_elaborated_lists_query),
            sqlparams=None, metadata=None
        )
        if elaborated_lists[0]:
            raise UserError(_(
                "Trying to cancel lists elaborated from WHS, "
                "please wait for cron synchronization or force it."
            ))
        check_elaborating_lists_query = \
            "SELECT * FROM HOST_LISTE WHERE NumLista = '%s' " \
            "AND Elaborato = 3" % (
                num_lista,
            )
        elaborating_lists = dbsource.execute_mssql(
            sqlquery=sql_text(check_elaborating_lists_query),
            sqlparams=None, metadata=None
        )
        if elaborating_lists[0]:
            raise UserError(_(
                "Trying to cancel lists launched in processing from user in WHS, "
                "please wait for order end processing."
            ))

    @api.multi
    def whs_check_list_state(self):
        # do no call super() and put specific code
        for whs_list in self:
            if whs_list.move_id:
                dbsource = self.env['base.external.dbsource'].search([
                    ('location_id', '=', whs_list.move_id.location_id.id)
                ])
                if not dbsource:
                    dbsource = self.env['base.external.dbsource'].search([
                        ('location_id', '=', whs_list.move_id.location_dest_id.id)
                    ])
                connection = dbsource.connection_open_mssql()
                if not connection:
                    raise UserError(_('Failed to open connection!'))
                whs_liste_query = \
                    "SELECT NumLista, NumRiga, Elaborato FROM HOST_LISTE " \
                    "WHERE NumLista = '%s' AND NumRiga = '%s'" % (
                        whs_list.num_lista, whs_list.riga)
                esito_lista = dbsource.execute_mssql(
                    sqlquery=sql_text(whs_liste_query), sqlparams=None, metadata=None
                )
                if not esito_lista[0]:
                    whs_liste_query_simple = \
                        "SELECT NumLista, Elaborato FROM HOST_LISTE " \
                        "WHERE NumLista = '%s'" % whs_list.num_lista
                    esito_lista_simple = dbsource.execute_mssql(
                        sqlquery=sql_text(whs_liste_query_simple), sqlparams=None,
                        metadata=None
                    )
                    if not esito_lista_simple[0]:
                        whs_liste_query_super_simple = \
                            "SELECT NumLista, Elaborato FROM HOST_LISTE " \
                            "WHERE NumLista like '%s'" % whs_list.num_lista.replace(
                                'WHS/', '')
                        esito_lista_super_simple = dbsource.execute_mssql(
                            sqlquery=sql_text(whs_liste_query_super_simple),
                            sqlparams=None,
                            metadata=None)
                        whs_list.write({
                            'whs_list_absent': True,
                            'whs_list_log': 'Query: %s result:\n [%s]\n'
                                            'Query simple: %s result:\n [%s]\n'
                                            'Query super simple: %s result:\n [%s]' % (
                                                whs_liste_query,
                                                str(esito_lista),
                                                whs_liste_query_simple,
                                                str(esito_lista_simple),
                                                whs_liste_query_super_simple,
                                                str(esito_lista_super_simple))
                        })
                    else:
                        whs_list.write({
                            'whs_list_absent': True,
                            'whs_list_log': 'Query: %s result:\n [%s]\n'
                                            'Query simple: %s result:\n [%s]' % (
                                                whs_liste_query,
                                                str(esito_lista),
                                                whs_liste_query_simple,
                                                str(esito_lista_simple))
                        })
                else:
                    whs_list.write({
                        'whs_list_absent': False,
                        'whs_list_log': 'Ok',
                    })

    @api.multi
    def whs_prepare_host_liste_values(self):
        # do no call super() and put specific code
        execute_params_order = {}
        for lista in self:
            if not execute_params_order.get(lista.num_lista):
                execute_params_order[lista.num_lista] = {}
            product = lista.product_id
            parent_product_id = lista.parent_product_id if lista.parent_product_id else False
            execute_params_order[lista.num_lista][lista.riga] = {
                'NumLista': lista.num_lista[:50],  # char 50
                'NumRiga': lista.riga,  # char 50 but is an integer
                'DataLista': lista.data_lista.strftime("%Y.%m.%d"),
                # formato aaaa.mm.gg datalista
                'Riferimento': lista.riferimento[:50] if lista.riferimento else '',  # char 50
                'TipoOrdine': lista.tipo,  # int
                'Causale': 10 if lista.tipo == '1' else 20,  # int
                'Priorita': lista.priorita,  # int
                'RichiestoEsito': 1,  # int
                'Stato': 0,  # int
                'ControlloEvadibilita': 0,  # int
                'Vettore': lista.vettore[:30] if lista.vettore else '',  # char 30
                'Indirizzo': lista.indirizzo[:50] if lista.indirizzo else '',  # char 50
                'Cap': lista.cap[:10] if lista.cap else '',  # char 10
                'Localita': lista.localita[:50] if lista.localita else '',  # char 50
                'Provincia': lista.provincia[:2] if lista.provincia else '',  # char 2
                'Nazione': lista.nazione[:50] if lista.nazione else '',  # char 50
                'Articolo': product.default_code[:30] if product.default_code
                else 'prodotto senza codice',  # char 30
                'DescrizioneArticolo': product.name[:70] if product.name
                else product.default_code[:70] if product.default_code
                else 'prodotto senza nome',  # char 70
                'Qta': lista.qta,  # numeric(18,3)
                'PesoArticolo': product.weight * 1000 if product.weight else 0,  # int
                'UMArticolo': 'PZ' if product.uom_id.name == 'Unit(s)'
                else product.uom_id.name[:10],  # char 10
                'IdTipoArticolo': 0,  # int
                'Elaborato': 0,  # 0 per poi scrivere 1 tutte insieme  # int
                'AuxTesto1': lista.client_order_ref[:50] if
                lista.client_order_ref else '',  # char 50
                'AuxTestoRiga1': lista.product_customer_code[:250] if
                lista.product_customer_code else '',  # char 250
                'AuxTestoRiga2': lista.product_customer_code[:250] if
                lista.product_customer_code else '',  # char 250
                'AuxTestoRiga3': (
                    parent_product_id.default_code[:250] if
                    parent_product_id.default_code else parent_product_id.name[:250]
                ) if parent_product_id else '',  # char 250
            }
            if lista.cliente:  # char 30
                execute_params_order[lista.num_lista][lista.riga].update({
                    'idCliente': lista.cliente[:30],
                })
            if lista.ragsoc:  # char 100
                execute_params_order[lista.num_lista][lista.riga].update({
                    'RagioneSociale': lista.ragsoc[:100],
                })
        execute_params_order_line = {}
        return execute_params_order, execute_params_order_line

    @api.multi
    def _get_set_liste_to_elaborate_query(self):
        # overridable method
        set_liste_to_elaborate_query = \
            "UPDATE HOST_LISTE SET Elaborato=1 WHERE Elaborato=0 " \
            "AND %s" % (
                " OR ".join(
                    "(NumLista='%s' AND NumRiga='%s')" % (
                        y.num_lista, y.riga) for y in self))
        return set_liste_to_elaborate_query
