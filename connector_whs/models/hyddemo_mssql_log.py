# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
import time

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

insert_product_query = """
INSERT INTO HOST_ARTICOLI (
Elaborato,
TipoOperazione,
Codice,
Descrizione,
Peso,
Barcode,
UM,
TipoConfezione,
CategoriaMerc,
MantieniDinamici,
Ubicazione,
Altezza,
Larghezza,
Profondita,
DescrizioneBreve,
ScortaMin,
Id
)
VALUES (
%(Elaborato)s,
%(TipoOperazione)s,
%(Codice)s,
%(Descrizione)s,
%(Peso)s,
%(Barcode)s,
%(UM)s,
%(TipoConfezione)s,
%(CategoriaMerc)s,
%(MantieniDinamici)s,
%(Ubicazione)s,
%(Altezza)s,
%(Larghezza)s,
%(Profondita)s,
%(DescrizioneBreve)s,
%(ScortaMin)s,
%(Id)s
)
"""

insert_host_liste_query = """
INSERT INTO HOST_LISTE (
NumLista,
NumRiga,
DataLista,
Riferimento,
TipoOrdine,
Causale,
Priorita,
RichiestoEsito,
Stato,
ControlloEvadibilita,
Vettore,
{idCliente}
{RagioneSociale}
Indirizzo,
Cap,
Localita,
Provincia,
Nazione,
Articolo,
DescrizioneArticolo,
Qta,
PesoArticolo,
UMArticolo,
IdTipoArticolo,
Elaborato,
AuxTesto1,
AuxTestoRiga1,
AuxTestoRiga2,
AuxTestoRiga3
) 
VALUES (
%(NumLista)s,
%(NumRiga)s,
%(DataLista)s,
%(Riferimento)s,
%(TipoOrdine)s,
%(Causale)s,
%(Priorita)s,
%(RichiestoEsito)s,
%(Stato)s,
%(ControlloEvadibilita)s,
%(Vettore)s,
{idClientes}
{RagioneSociales}
%(Indirizzo)s,
%(Cap)s,
%(Localita)s,
%(Provincia)s,
%(Nazione)s,
%(Articolo)s,
%(DescrizioneArticolo)s,
%(Qta)s,
%(PesoArticolo)s,
%(UMArticolo)s,
%(IdTipoArticolo)s,
%(Elaborato)s,
%(AuxTesto1)s,
%(AuxTestoRiga1)s,
%(AuxTestoRiga2)s,
%(AuxTestoRiga3)s
)
"""


class HyddemoMssqlLog(models.Model):
    _name = "hyddemo.mssql.log"
    _description = "Synchronization with Remote Mssql DB"
    _order = 'ultimo_invio desc'

    ultimo_id = fields.Integer('Last ID in WHS', default=1)
    ultimo_invio = fields.Datetime('Last Processing', readonly=True)
    errori = fields.Text('Log Processing', readonly=True)
    dbsource_id = fields.Many2one(
        'base.external.dbsource',
        'External DB Source Origin',
        readonly=True)
    inventory_id = fields.Many2one(
        'stock.inventory',
        'Created inventory',
        readonly=True)
    hyddemo_mssql_log_line_ids = fields.One2many(
        'hyddemo.mssql.log.line',
        'hyddemo_mssql_log_id',
        'Log lines'
    )

    @api.model
    def whs_update_products(self, datasource_id):
        """
        Send to HOST_ARTICOLI table only the products changed from the last execution,
        which will be picked up by WHS software.
        """
        dbsource_obj = self.env['base.external.dbsource']
        dbsource = dbsource_obj.browse(datasource_id)
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_('Failed to open connection!'))
        # delete from HOST_ARTICOLI if already processed from WHS (Elaborato=2)
        # or interrupted (bad) records (Elaborato=0)
        clean_product_query = \
            "DELETE FROM HOST_ARTICOLI WHERE Elaborato = 2 OR Elaborato = 0"
        dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=clean_product_query, sqlparams=None, metadata=None)
        log_data = self.search_read(
            [], ['ultimo_invio', 'ultimo_id'], order='ultimo_id desc', limit=1)
        _logger.info(log_data)
        last_id = log_data[0]['ultimo_id']
        last_date_dt = log_data[0]['ultimo_invio']
        last_date = fields.Datetime.to_string(last_date_dt)
        products = self.env['product.product'].search([
            '|', ('write_date', '>', last_date),
            ('product_tmpl_id.write_date', '>', last_date),
            ('type', '=', 'product'),
            ('exclude_from_whs', '!=', True),
        ])
        new_last_update = fields.Datetime.now()
        for product in products:
            insert_product_params = self._prepare_host_articoli_values(
                product, dbsource.warehouse_id.id, dbsource.location_id.id, last_id)
            dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=insert_product_query.replace('\n', ' '),
                sqlparams=insert_product_params,
                metadata=None)

        # Set record from Elaborato=0 to Elaborato=1 to be processable from WHS
        update_product_query = \
            "UPDATE HOST_ARTICOLI SET Elaborato = 1 WHERE Elaborato = 0"
        dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=update_product_query, sqlparams=None, metadata=None)
        res = self.env['hyddemo.mssql.log'].create({
            'ultimo_invio': new_last_update,
            'errori': 'Added %s products' % len(products),
            'dbsource_id': datasource_id,
        })
        _logger.info(res)
        dbsource.connection_close_mssql(connection)
        return True

    @api.multi
    def _prepare_host_articoli_values(
            self, product, warehouse_id, location_id, last_id):
        ops = self.env['stock.warehouse.orderpoint'].search([
            ('warehouse_id', '=', warehouse_id),
            ('location_id', '=', location_id),
            ('product_id', '=', product.id),
        ])
        if len(ops) > 1:
            pass
        product_min_qty = ops[0].product_min_qty if ops else 0
        """
        Elaborato:
            ('0', 'In elaborazione da host'),
            ('1', 'Elaborabile da whs'),
            ('2', 'Elaborato da whs'),
        TipoOperazione
            ('A', 'aggiungi se non esiste, modifica se già inserito'),
            ('C', 'rimuovi il codice dal database WHS solo se non utilizzato'),
        """
        execute_params = {
            'Elaborato': 0,
            'TipoOperazione': 'A',
            'Codice': product.default_code[:75] if product.default_code
            else 'articolo senza codice',
            'Descrizione': product.name[:70],
            'Peso': product.weight * 1000 if product.weight else 0.0,  # digits=(18, 5)
            'Barcode': product.barcode[:30] if product.barcode else ' ',
            'UM': 'PZ' if product.uom_id.name == 'Unit(s)' else product.uom_id.name[:10],
            'TipoConfezione': 0,
            'CategoriaMerc': ' ',  # size=10
            'MantieniDinamici': 1,
            'Ubicazione': ' ',
            'Altezza': 0,
            'Larghezza': 0,
            'Profondita': 0,
            'DescrizioneBreve': ' ',
            'ScortaMin': product_min_qty,  # digits=(18, 3)
            'Id': last_id + 1,
        }
        return execute_params

    @api.model
    def whs_check_list_state(self, datasource_id):
        """
        Funzione lanciabile manualmente per marcare le liste in Odoo che non sono più
        presenti in WHS in quanto cancellate, per verifiche
        :param datasource_id:
        :return:
        """
        dbsource_obj = self.env['base.external.dbsource']
        dbsource = dbsource_obj.browse(datasource_id)
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_('Failed to open connection!'))
        whs_lists = self.env['hyddemo.whs.liste'].search([
            ('stato', 'in', ['1', '2']),
        ])
        i = 0
        imax = len(whs_lists)
        step = 1
        for whs_list in whs_lists:
            whs_liste_query = \
                "SELECT NumLista, NumRiga, Qta, QtaMovimentata, Elaborato " \
                "FROM HOST_LISTE "\
                "WHERE NumLista = '%s' AND NumRiga = '%s'" % (
                    whs_list.num_lista, whs_list.riga)
            esiti_liste = dbsource.execute_mssql(
                sqlquery=whs_liste_query, sqlparams=None, metadata=None)
            # esiti_liste[0] contains result
            if not esiti_liste[0]:
                whs_list.whs_list_absent = True
            else:
                whs_list.whs_list_absent = False
            i += 1
            if i * 100.0 / imax > step:
                _logger.info(
                    'WHS LOG: Execution {0}% '.format(
                        int(i * 100.0 / imax)))
                step += 1

    @api.model
    def whs_read_and_synchronize_list(self, datasource_id):
        """
        Funzione lanciabile tramite cron per aggiornare i movimenti dalle liste create
        per WHS da Odoo nei vari moduli collegati (mrp, stock, ecc.)
        :param datasource_id:
        :return:
        """
        dbsource_obj = self.env['base.external.dbsource']
        dbsource = dbsource_obj.browse(datasource_id)
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_('Failed to open connection!'))
        i = 0
        pickings_to_assign = self.env['stock.picking']
        while True:
            # read 1000 record instead of 100 as in the past version
            # for test use Elaborato=1 instead of 4 and manually change qty_moved in
            # debug
            esiti_liste_query = \
                "SELECT * FROM (SELECT row_number() OVER (ORDER BY NumLista, NumRiga) "\
                "AS rownum, NumLista, NumRiga, Qta, QtaMovimentata, Lotto, Lotto2, "\
                "Lotto3, Lotto4, Lotto5 FROM HOST_LISTE WHERE Elaborato=4) AS A "\
                "WHERE A.rownum BETWEEN %s AND %s" % (i, i + 1000)
            i += 1000
            esiti_liste = dbsource.execute_mssql(
                sqlquery=esiti_liste_query, sqlparams=None, metadata=None)
            # esiti_liste[0] contain result
            if not esiti_liste[0]:
                break
            for esito_lista in esiti_liste[0]:
                num_lista = esito_lista[1]
                num_riga = int(esito_lista[2])
                if not num_riga or not num_lista:
                    _logger.debug(
                        'WHS LOG: list %s in db without NumLista or NumRiga' %
                        esito_lista)
                    continue
                hyddemo_whs_lists = self.env['hyddemo.whs.liste'].search([
                    ('num_lista', '=', num_lista),
                    ('riga', '=', num_riga)
                ])
                if not hyddemo_whs_lists:
                    # ROADMAP: if the user want to create the list directly in WHS, do
                    # the reverse synchronization (not requested so far)
                    _logger.debug(
                        'WHS LOG: list num_riga %s num_lista %s not found in '
                        'lists (found list %s but not row)' % (
                            num_riga,
                            num_lista,
                            self.env['hyddemo.whs.liste'].search([
                                ('num_lista', '=', num_lista)]),
                            )
                        )
                    continue
                if len(hyddemo_whs_lists) > 1:
                    _logger.info(
                        'WHS LOG: More than 1 list found for lista %s' %
                        hyddemo_whs_lists)
                hyddemo_whs_list = hyddemo_whs_lists[0]
                if hyddemo_whs_list.stato == '3':
                    _logger.debug('WHS LOG: list not processable: %s-%s' % (
                        hyddemo_whs_list.num_lista,
                        hyddemo_whs_list.riga,
                    ))
                    continue
                move = hyddemo_whs_list.move_id

                try:
                    qty_moved = float(esito_lista[4])
                except ValueError:
                    qty_moved = False
                    pass
                except TypeError:
                    qty_moved = False
                    pass

                lotto = esito_lista[5].strip() if esito_lista[5] else False
                lotto2 = esito_lista[6].strip() if esito_lista[6] else False
                lotto3 = esito_lista[7].strip() if esito_lista[7] else False
                lotto4 = esito_lista[8].strip() if esito_lista[8] else False
                lotto5 = esito_lista[9].strip() if esito_lista[9] else False

                if not qty_moved or qty_moved == 0.0:
                    # nothing to-do as not moved
                    continue
                elif qty_moved != hyddemo_whs_list.qta:
                    # in or out differs from total qty
                    if qty_moved > hyddemo_whs_list.qta:
                        _logger.info('WHS LOG: list %s: qty moved %s is bigger than '
                                     'initial qty %s!'
                                     % (hyddemo_whs_list.id, qty_moved,
                                        hyddemo_whs_list.qta))

                # set reserved availability on qty_moved if != 0.0 and with max of
                # whs list qta
                move.reserved_availability = min(qty_moved, hyddemo_whs_list.qta)

                # Set move qty_moved user can create a backorder
                # Picking become automatically done if all moves are done
                hyddemo_whs_list.write({
                    'stato': '4',
                    'qtamov': qty_moved,
                    'lotto': lotto,
                    'lotto2': lotto2,
                    'lotto3': lotto3,
                    'lotto4': lotto4,
                    'lotto5': lotto5,
                })
                if move.move_line_ids:
                    move.move_line_ids[0].qty_done = qty_moved
                else:
                    _logger.info('WHS LOG: Missing move lines in move %s' % move.name)
                if move.picking_id.mapped('move_lines').filtered(
                        lambda m: m.state not in ('draft', 'cancel', 'done')):
                    # FIXME action_assign must assign on qty_done and not on available
                    pickings_to_assign |= move.picking_id

                # Set mssql list done from host, they are not deleted from HOST to
                # preserve history, but it is a possible implementation to do
                set_liste_to_done_query = \
                    "UPDATE HOST_LISTE SET Elaborato=5 WHERE NumLista='%s' AND "\
                    "NumRiga='%s'" % (num_lista, num_riga)
                dbsource.with_context(no_return=True).execute_mssql(
                    sqlquery=set_liste_to_done_query, sqlparams=None,
                    metadata=None)
        if pickings_to_assign:
            pickings_to_assign.action_assign()

    @api.multi
    def whs_insert_list_to_elaborate(self, datasource_id):
        """
        Write on mssql the lists in stato 1 created from stock and repair in
        hyddemo.whs.liste to be elaborated from WHS
        :param datasource_id:
        :return:
        """
        dbsource_obj = self.env['base.external.dbsource']
        dbsource = dbsource_obj.browse(datasource_id)
        connection = dbsource.connection_open_mssql()
        if not connection:
            raise UserError(_('Failed to open connection!'))

        hyddemo_whs_lists = self.env['hyddemo.whs.liste'].search([
            ('stato', '=', '1'),
        ])
        for lista in hyddemo_whs_lists:
            insert_esiti_liste_params = self._prepare_host_liste_values(lista)
            insert_query = self.get_insert_query(insert_esiti_liste_params)
            if insert_esiti_liste_params:
                self.execute_query(dbsource, insert_query, insert_esiti_liste_params)
        # Update lists on mssql from 0 to 1 to be elaborated from WHS all in the same
        # time
        if hyddemo_whs_lists:
            set_liste_to_elaborate_query = \
                "UPDATE HOST_LISTE SET Elaborato=1 WHERE Elaborato=0 " \
                "AND %s" % (
                    " OR ".join(
                        "(NumLista='%s' AND NumRiga='%s')" % (
                            y.num_lista, y.riga) for y in hyddemo_whs_lists))
            dbsource.with_context(no_return=True).execute_mssql(
                sqlquery=set_liste_to_elaborate_query, sqlparams=None,
                metadata=None)
            hyddemo_whs_lists.write({'stato': '2'})
        # commit to exclude rollback as mssql wouldn't be rollbacked too
        self._cr.commit()  # pylint: disable=E8102
        self.whs_read_and_synchronize_list(datasource_id)

    @staticmethod
    def get_insert_query(insert_esiti_liste_params):
        if 'idCliente' in insert_esiti_liste_params:
            if 'RagioneSociale' in insert_esiti_liste_params:
                insert_query = insert_host_liste_query.format(
                    idCliente='idCliente,',
                    idClientes='%(idCliente)s,',
                    RagioneSociale='RagioneSociale,',
                    RagioneSociales='%(RagioneSociale)s,'
                )
            else:
                insert_query = insert_host_liste_query.format(
                    idCliente='idCliente,',
                    idClientes='%(idCliente)s,',
                    RagioneSociale='',
                    RagioneSociales=''
                )
        elif 'RagioneSociale' in insert_esiti_liste_params:
            insert_query = insert_host_liste_query.format(
                RagioneSociale='RagioneSociale,',
                RagioneSociales='%(RagioneSociale)s,',
                idCliente='',
                idClientes=''
            )
        else:
            insert_query = insert_host_liste_query.format(
                RagioneSociale='',
                RagioneSociales='',
                idCliente='',
                idClientes=''
            )
        return insert_query

    def execute_query(self, dbsource, insert_query, insert_esiti_liste_params):
        res = dbsource.with_context(no_return=True).execute_mssql(
            sqlquery=insert_query.replace('\n', ' '),
            sqlparams=insert_esiti_liste_params,
            metadata=None)
        if not res:
            time.sleep(1)
            self.execute_query(dbsource, insert_query, insert_esiti_liste_params)
        return res

    @api.multi
    def _prepare_host_liste_values(self, hyddemo_whs_list):
        product = hyddemo_whs_list.product_id
        parent_product_id = hyddemo_whs_list.parent_product_id \
            if hyddemo_whs_list.parent_product_id else False
        execute_params = {
            'NumLista': hyddemo_whs_list.num_lista[:50],  # char 50
            'NumRiga': hyddemo_whs_list.riga,  # char 50 but is an integer
            'DataLista': hyddemo_whs_list.data_lista.strftime("%Y.%m.%d"),
            # formato aaaa.mm.gg datalista
            'Riferimento': hyddemo_whs_list.riferimento[:50] if
            hyddemo_whs_list.riferimento else '',  # char 50
            'TipoOrdine': hyddemo_whs_list.tipo,  # int
            'Causale': 10 if hyddemo_whs_list.tipo == '1' else 20,  # int
            'Priorita': hyddemo_whs_list.priorita,  # int
            'RichiestoEsito': 1,  # int
            'Stato': 0,  # int
            'ControlloEvadibilita': 0,  # int
            'Vettore': hyddemo_whs_list.vettore[:30] if
            hyddemo_whs_list.vettore else '',  # char 30
            'Indirizzo': hyddemo_whs_list.indirizzo[:50] if
            hyddemo_whs_list.indirizzo else '',  # char 50
            'Cap': hyddemo_whs_list.cap[:10] if
            hyddemo_whs_list.cap else '',  # char 10
            'Localita': hyddemo_whs_list.localita[:50] if
            hyddemo_whs_list.localita else '',  # char 50
            'Provincia': hyddemo_whs_list.provincia[:2] if
            hyddemo_whs_list.provincia else '',  # char 2
            'Nazione': hyddemo_whs_list.nazione[:50] if
            hyddemo_whs_list.nazione else '',  # char 50
            'Articolo': product.default_code[:30] if product.default_code
            else 'prodotto senza codice',  # char 30
            'DescrizioneArticolo': product.name[:70] if product.name
            else product.default_code[:70] if product.default_code
            else 'prodotto senza nome',  # char 70
            'Qta': hyddemo_whs_list.qta,  # numeric(18,3)
            'PesoArticolo': product.weight * 1000 if product.weight else 0,  # int
            'UMArticolo': 'PZ' if product.uom_id.name == 'Unit(s)'
            else product.uom_id.name[:10],  # char 10
            'IdTipoArticolo': 0,  # int
            'Elaborato': 0,  # 0 per poi scrivere 1 tutte insieme  # int
            'AuxTesto1': hyddemo_whs_list.client_order_ref[:50] if
            hyddemo_whs_list.client_order_ref else '',  # char 50
            'AuxTestoRiga1': hyddemo_whs_list.product_customer_code[:250] if
            hyddemo_whs_list.product_customer_code else '',  # char 250
            'AuxTestoRiga2': hyddemo_whs_list.product_customer_code[:250] if
            hyddemo_whs_list.product_customer_code else '',  # char 250
            'AuxTestoRiga3': (
                parent_product_id.default_code[:250] if
                parent_product_id.default_code else parent_product_id.name[:250]
            ) if parent_product_id else '',  # char 250
        }
        if hyddemo_whs_list.cliente:  # char 30
            execute_params.update({'idCliente': hyddemo_whs_list.cliente[:30]})
        if hyddemo_whs_list.ragsoc:  # char 100
            execute_params.update({'RagioneSociale': hyddemo_whs_list.ragsoc[:100]})
        return execute_params


class HyddemoMssqlLogLine(models.Model):
    _name = "hyddemo.mssql.log.line"
    _description = "Mssql Log Line"

    name = fields.Text()
    qty_wrong = fields.Float()
    qty = fields.Float()
    weight = fields.Float()
    weight_wrong = fields.Float()
    product_id = fields.Many2one(
        'product.product')
    type = fields.Selection([
        ('not_found', 'Not found'),
        ('ok', 'Ok'),
        ('mismatch', 'Mismatch'),
        ('service', 'Service'),
    ], 'Type')
    lot = fields.Text()
    hyddemo_mssql_log_id = fields.Many2one(
        'hyddemo.mssql.log')
