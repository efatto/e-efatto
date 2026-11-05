Questo modulo introduce una logica di produzione in parallelo per prodotti con seriale univoco, che di default sono prodotti uno alla volta.

La produzione di origine viene copiata per mantenerla come riferimento, rimuovendo i collegamenti ai trasferimenti e alle origini, che verranno collegati alle lavorazioni dei seriali.

In questa produzione vanno registrati i tempi di lavorazione, che sono suddivisi all'interno delle lavorazioni figlie. È anche possibile registrare dei tempi specifici aggiuntivi all'interno delle lavorazioni figlie.

![Produzione seriale in parallelo](../static/description/produzione_seriale_in_parallelo.png)

RIMOSSO IN QUANTO NON USATO: Nelle produzioni figlie è possibile impostare i prodotti consumati singolarmente. Poi si possono completare tutte contemporaneamente dalla produzione padre.
N.B. Attualmente si può solo eseguire la produzione in parallelo direttamente, in seguito è comunque possibile sbloccare le produzioni figlie completate per modificare o azzerare le quantità dei componenti consumati oppure aggiungerne di nuovi.

I passaggi da eseguire per la produzione in parallelo sono:

1. Crea una produzione e imposta la quantità da produrre per almeno 2 pezzi (se da 1 solo pezzo la produzione funziona normalmente)
2. Conferma la produzione
3. assegna i numeri seriali riservati, da creare a parte:

![Lotti riservati](../static/description/lotti_riservati.png)

4. registra le ore lavorate sulla produzione: verranno poi suddivise equamente tra le produzioni singole generate per ogni seriale
5. completa la produzione padre, che completerà tutte le produzioni figlie, con il bottone:

![Matrice numeri seriali](../static/description/matrice_numeri_seriali.png)

che apre una maschera precompilata con i seriali da produrre, in cui usare il bottone `Valida`:

![Valida](../static/description/valida.png)

In questa maschera verranno richiesti eventuali seriali per i componenti utilizzati, se necessari.

6. POSSIBILITÀ RIMOSSA IN QUANTO NON USATA E NON TESTATA: facoltatimente, prepara le produzioni figlie e registra le ore singolarmente, che verranno aggiunte a quelle suddivise inserite dalla produzione padre

![Prepara](../static/description/prepara.png)

IMPORTANTE: se il trasferimento alla produzione è impostato con l'opzione di "Annullare movimento successivo", nel caso in cui sia impostato nel magazzino l'opzione "Prelievo componenti e produzione (2 fasi)", se il trasferimento verso l'ubicazione della produzione viene annullato, verranno annullati anche i movimenti di scarico dei componenti, bloccando la produzione in parallelo. Si raccomanda quindi di togliere questa opzione, oppure di eseguire i trasferimenti in maniera completa, oppure di completare la produzione prima di annullare i trasferimenti.
