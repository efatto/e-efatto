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

È possibile decidere se i movimenti vengono creati ed inviati al WMS con
due modalità:

1.  immediatamente quando il trasferimento è confermato: con questa
    opzione Odoo viene aggiornato in base ai movimenti eseguiti nella
    macchina WMS collegata;
2.  a posteriori quando il trasferimento è completato: con questa
    opzione i trasferimenti vengono eseguiti in Odoo come di norma e
    vengono inviati da eseguire come già deciso. Nel caso di una
    esecuzione con quantità diversa il sistema aggiornerà il magazzino
    con una rettifica di inventario, per cui la giacenza a magazzino
    sarà corretta ma movimentata in maniera diversa. In particolare, se
    ad esempio c'è una consegna di 5 pezzi e la consegna effettiva è di
    4 pezzi, la consegna in Odoo resterà come previsto e ci sarà una
    rettifica di magazzino in aumento di 1 pezzo.

![Opzione avvio WMS](../static/description/opzione_avvio.png)

Normalmente le liste al WMS sono inviate e lette per la sincronizzazione
tramite un'azione programmata, è comunque possibile anche il solo invio
immediatamente, poi la sincronizzazione procederà comunque come al
solito:

![Invio immediato al WMS](../static/description/invio_immediato.png)

Nelle righe dei trasferimenti è presente questa icona per accedere alle
liste del WMS, visibile solo se ci sono:

![Opzione avvio WMS](../static/description/icona_liste.png)

![Processo di produzione]

Il processo di produzione è modificato rispetto al default:

#. alla conferma della produzione vengono create le liste che poi verranno
inviate al WMS per la sincronizzazione
#. nel WMS l'operatore procederà quindi all'elaborazione delle liste
#. solo da questo momento in Odoo sarà possibile "consumare" i componenti
utilizzati dalla produzione, la cui quantità sarà stata inserita
automaticamente dal sincronizzatore. Il bottone "Consuma" completa i movimenti
di magazzino, che saranno quindi quelli effettivamente eseguiti nel WMS.
#. a questo punto sarà possibile generare i prodotti finiti con il bottone
"Produci", la cui quantità sarà calcolata in base alla quantità da produrre
impostata nella produzione (per eventuali scarti va utilizzata l'apposita
procedura).
