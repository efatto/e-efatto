# Copyright 2022 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models

# todo CREARE UN modello per salvare i dati in maniera provvisoria, inviati dall'IOT
#  ad ogni x secondi, ed utilizzare quelli per gestire la produzione a seguito dell'
#  intervento utente, che dovrà avviare la produzione e poi far partire la macchina,
#  quindi terminarla quando la macchina è ferma
#  Creare un campo aggiuntivo collegato nella produzione per indicare in quale centro
#  di lavoro è gestita la produzione. Mettere un blocco per evitare che ci siano più
#  produzioni attive sullo stesso centro di lavoro (macchina), in quanto l'IOT prenderà
#  la prima produzione in corso su quel centro di lavoro, senza essere a conoscenza di
#  nulla.
#  Salvare nella produzione il numero di sacchi attuali all'inizio della produzione e
#  quelli finali alla fine, per calcolare i sacchi prodotti.

#  ANNULLATO
#  Utilizzare l'IOT OUTPUT creando una funzione che metta a disposizione un controller
#  di tipo GET per ricevere il tipo di lavorazione da fare per la produzione, di cui
#  si occupa il programma in modbus di chiamare.
#  Creare un campo numerico intero nella distinta base in cui scegliere la ricetta, che
#  verrà prelevata dal GET tramite la funzione IOT OUTPUT.

#  È emersa una proposta da parte di Beccaria, ma non è confermata.
#  Verrà inviato il nome dell'ordine di produzione e lo stato "in attesa".


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model
    def input_production_produce(self, **kwargs):
        res = False
        product_qty = 1
        product_lot = False
        production = False
        domain = [('state', 'not in', ['done', 'cancel'])]
        log_msg = ''
        for key, value in kwargs.items():
            if key == 'value':
                production_name = value
                domain.append(('name', '=', value))
                productions = self.env['mrp.production'].search(domain)
                if not productions:
                    log_msg += 'Production %s not found' % production_name
                    break
                if len(productions) > 1:
                    log_msg += 'More production %s found' % production_name
                production = productions[0]
            if key == 'product_lot':
                product_lot = value
            if key == 'product_qty':
                product_qty = int(value)
        if production:
            values = {
                'production_id': production.id,
                'product_id': production.product_id.id,
                'product_qty': product_qty,
                'product_uom_id': production.product_uom_id.id,
            }
            if product_lot:
                lot_id = False
                lot_ids = self.env['stock.production.lot'].search([
                    ('name', '=', product_lot),
                ])
                if not lot_ids:
                    lot_id = self.env['stock.production.lot'].create([{
                        'product_id': production.product_id.id,
                        'name': product_lot,
                    }])
                    log_msg += 'Created new lot %s' % product_lot
                elif len(lot_ids) > 1:
                    log_msg += 'More lot %s found' % product_lot
                    lot_id = lot_ids[0]
                if lot_id:
                    values.update(
                        dict(lot_id=lot_id.id)
                    )
            produce = self.env['mrp.product.produce'].with_context(
                default_production_id=production.id,
                active_id=production.id).create(values)
            produce._onchange_product_qty()
            res = produce.do_produce()
        if not res:
            return {'status': 'error', 'message': log_msg}
        return {'status': 'ok', 'message': 'Production done'}

    @api.model
    def input_production_weight(self, **kwargs):
        res = False
        production_weight = 0
        production = False
        # limit weight ability to progress state
        domain = [('state', '=', 'progress'), ('check_to_done', '=', True)]
        log_msg = ''
        weight_uom_cat_id = self.env['uom.category'].search([
            ('measure_type', '=', 'weight')
        ])[0]
        reference_weight_uom_id = self.env['uom.uom'].search([
            ('category_id', '=', weight_uom_cat_id.id),
            ('uom_type', '=', 'reference'),
        ])
        for key, value in kwargs.items():
            if key == 'value':
                production_name = value
                domain.append(('name', '=', value))
                productions = self.env['mrp.production'].search(domain)
                if not productions:
                    log_msg += 'Production %s not found or not in progress' \
                               % production_name
                    break
                if len(productions) > 1:
                    log_msg += 'More production %s found' % production_name
                production = productions[0]
            if key == 'production_weight':
                production_weight = value
        if production:
            if not production_weight:
                log_msg += 'Missing production %s weight' % production.name
            else:
                # set moves weight proportionally to weight received
                moves = production.move_raw_ids.filtered(
                    lambda x: x.product_uom.category_id == weight_uom_cat_id
                )
                # sum all weights converted to reference uom weight
                total_weight = sum(
                    x.product_uom._compute_quantity(
                        x.product_uom_qty,
                        reference_weight_uom_id,
                        round=False)
                    for x in moves
                )
                if total_weight:
                    coef = production_weight / total_weight
                    for move in moves:
                        move.product_uom_qty = move.product_uom_qty * coef
                    res = True
        if not res:
            return {'status': 'error', 'message': log_msg}
        return {'status': 'ok', 'message': 'Production weighted'}
