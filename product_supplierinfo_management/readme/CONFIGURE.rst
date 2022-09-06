Questo modulo mette a disposizione delle funzionalità per verificare l'attendibilità dei prezzi di acquisto dei prodotti e per aggiornare il costo o il costo di sostituzione in base a questi prezzi.

I prodotti vengono considerati solo se hanno un fornitore o un acquisto o una fattura d'acquisto e sono acquistabili, la presenza o meno di una distinta di produzione non viene considerata (questo modulo non dipende dalla produzione).

Il nuovo costo viene calcolato tramite il listino collegato, che si può basare o meno sul prezzo del fornitore collegato (tramite l'utilizzo del modulo product_pricelist_supplierinfo). Nel listino è necessario abilitare l'opzione "Abilita Gestione Prezzi Fornitori" perché sia utilizzabile a questo scopo:

.. image:: ../static/description/abilita-listino.png
    :alt: Abilita listino

Il menu creato dal modulo mette a disposizione quattro azioni:

.. image:: ../static/description/menu.png
    :alt: Menu in impostazioni Magazzino

La prima esegue il solo controllo dei prezzi:

.. image:: ../static/description/controllo.png
    :alt: Controllo prezzi

La seconda esegue l'aggiornamento del costo:

.. image:: ../static/description/aggiorna_costo.png
    :alt: Aggiorna il costo

La terza esegue l'aggiornamento del costo di sostituzione:

.. image:: ../static/description/aggiorna_sostituzione.png
    :alt: Aggiorna il costo di sostituzione

N.B.: Non è possibile ripristinare questa operazione, per cui il campo costo da ora in poi sarà questo. Tenere conto in ogni caso che questo campo potrebbe essere modificato in maniera automatica dal sistema in base alla configurazione.

La quarta copia il costo di sostituzione sul costo del prodotto:

.. image:: ../static/description/copia.png
    :alt: Copia

N.B.: Nel caso sia installato il modulo https://github.com/sergiocorato/e-efatto/tree/12.0/product_pricelist_replenishment_cost è possibile impostare i listini di vendita sulla base del costo di sostituzione, su cui sarà calcolato il margine di vendita, senza andare a toccare il costo del prodotto.

Dettaglio del funzionamento:

#. se il prodotto non ha fornitori con data di validità in corso e prezzo diverso da zero e non ci sono ultime fatture o ultimi acquisti, il nuovo costo viene calcolato dal costo del prodotto con la regola del listino selezionato;
#. (i prodotti di cui sopra con il nuovo costo pari a zero vengono mostrati in "Prodotti a costo calcolato zero senza acquisto né fattura")
#. (i prodotti di cui sopra senza un fornitore valido vengono mostrati in 'Prodotti senza fornitore')

Tra i prodotti con fornitore valido:

#. viene selezionato il primo fornitore valido, gli altri sono ignorati
#. se è indicata la Data Obsolescenza Prezzi Fornitori, i prodotti con la data di ultima modifica del prezzo di questo fornitore precedente alla data indicata vengono mostrati nei 'Prodotti con prezzo fornitore obsoleto';
#. se il prodotto ha un ultimo acquisto:
    #. se l'ultimo fornitore è diverso dal fornitore valido, viene mostrato in 'Prodotti con fornitore non coincidente';
    #. se l'ultimo acquisto è diverso è più recente dell'ultimo prezzo fornitore, viene calcolato il nuovo costo dal costo dell'ultimo acquisto con la regola del listino selezionato;
    #. (i prodotti di cui sopra con il nuovo costo pari a zero vengono mostrati in "Prodotti a costo calcolato zero con acquisto")
#. altrimenti, se il prodotto ha un'ultima fattura:
    #. se l'ultima fattura è di un fornitore diverso dal fornitore valido, viene mostrato in 'Prodotti con fornitore non coincidente';
    #. se l'ultimo acquisto da fattura è diverso e più recente dell'ultimo prezzo fornitore, viene calcolato il nuovo costo dal costo dell'ultima fattura con la regola del listino selezionato;
    #. (i prodotti di cui sopra con il nuovo costo pari a zero vengono mostrati in "Prodotti a costo calcolato zero con fattura")
#. per i prodotti senza ultima fattura né ultimo acquisto:
    #. viene calcolato il nuovo costo dal costo del fornitore valido;
    #. (i prodotti di cui sopra con il nuovo costo pari a zero vengono mostrati in "Prodotti a costo calcolato zero con acquisto o fattura più vecchi")
