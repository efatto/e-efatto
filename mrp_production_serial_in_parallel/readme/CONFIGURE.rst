Questo modulo introduce una logica di produzione in parallelo per prodotti con seriale univoco, che di default sono prodotti uno alla volta.

La produzione di origine viene copiata per mantenerla come riferimento, rimuovendo i collegamenti ai trasferimenti e alle origini, che verranno collegati alle lavorazioni dei seriali.

In questa produzione vanno registrati i tempi di lavorazione, che sono suddivisi all'interno delle lavorazioni figlie. È anche possibile registrare dei tempi specifici aggiuntivi all'interno delle lavorazioni figlie.

.. image:: ../static/description/produzione_seriale_in_parallelo.png
    :alt: Produzione seriale in parallelo

Nelle produzioni figlie è possibile impostare i prodotti consumati singolarmente. Poi si possono completare tutte contemporaneamente dalla produzione padre.

I passaggi da eseguire per la produzione in parallelo sono:

#. Crea una produzione e imposta la quantità da produrre per almeno 2 pezzi (se da 1 solo pezzo la produzione funziona normalmente)

#. Conferma la produzione

#. assegna i numeri seriali riservati, da creare a parte:

.. image:: ../static/description/lotti_riservati.png
    :alt: Lotti riservati

#. registra le ore lavorate sulla produzione: verranno poi suddivise equamente tra le produzioni singole generate per ogni seriale


#. completa la produzione padre, che completerà tutte le produzioni figlie, con il bottone:

.. image:: ../static/description/matrice_numeri_seriali.png
    :alt: Matrice numeri seriali

che apre una maschera precompilata con i seriali da produrre, in cui usare il bottone `Valida`:

.. image:: ../static/description/valida.png
    :alt: Valida

In questa maschera verranno richiesti eventuali seriali per i componenti utilizzati, se necessari.

#.a facoltatimente, prepara le produzioni figlie e registra le ore singolarmente, che verranno aggiunte a quelle suddivise inserite dalla produzione padre

.. image:: ../static/description/prepara.png
    :alt: Prepara
