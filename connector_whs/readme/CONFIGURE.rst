La connessione con il database del software del magazzino viene configurata nelle sorgenti database:

.. image:: ../static/description/sorgenti_database.png
    :alt: Sorgenti database

In questa maschera vanno indicati i dati per la connessione con la stringa e l'eventuale stringa per la connessione al database di test, il magazzino collegato e altri:

.. image:: ../static/description/configurazione_sorgente_dati.png
    :alt: Configurazione sorgente dati

Dalla sorgente dati sono disponibile alcune azioni. La seguente va a caricare nella tabella di scambio i prodotti modificati dall'ultima esecuzione, che verranno prelevati e aggiornati nel software collegato:

.. image:: ../static/description/aggiorna_prodotti.png
    :alt: Aggiorna prodotti

Questa azione forza l'aggiornamento delle liste:

.. image:: ../static/description/sincronizza_liste.png
    :alt: Sincronizza liste

Quest'ultima l'inventario dei prodotti:

.. image:: ../static/description/sincronizza_magazzino.png
    :alt: Sincronizza magazzino

Nella sorgente dati è necessario configurare quali tipi di movimento sono gestiti tramite il WMS. In caso di configurazione tramite 2 step, vanno solitamente esclusi i trasferimenti dalle posizioni di Output e Input, per evitare un doppio scarico/carico dal WMS.
