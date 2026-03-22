La connessione con il database del software del magazzino viene
configurata nelle sorgenti database:

![Sorgenti database](../static/description/sorgenti_database.png)

In questa maschera vanno indicati i dati per la connessione con la
stringa e l'eventuale stringa per la connessione al database di test, il
magazzino collegato e altri:

![Configurazione sorgente dati](../static/description/configurazione_sorgente_dati.png)

Dalla sorgente dati sono disponibile alcune azioni. La seguente va a
caricare nella tabella di scambio i prodotti modificati dall'ultima
esecuzione, che verranno prelevati e aggiornati nel software collegato:

![Aggiorna prodotti](../static/description/aggiorna_prodotti.png)

Questa azione forza l'aggiornamento delle liste:

![Sincronizza liste](../static/description/sincronizza_liste.png)

Quest'ultima l'inventario dei prodotti:

![Sincronizza magazzino](../static/description/sincronizza_magazzino.png)

Nella sorgente dati è necessario configurare quali tipi di movimento
sono gestiti tramite il WMS. In caso di configurazione tramite 2 step,
vanno solitamente esclusi i trasferimenti dalle posizioni di Output e
Input, per evitare un doppio scarico/carico dal WMS.
