Questo modulo permette di eseguire diversi ordini di lavoro in parallelo su diversi centri di lavoro.
Non permette di farli sullo stesso centro di lavoro, come è previsto di default dal sistema originale.

La pianificazione degli ordini in parallelo parte dallo stesso momento e comunque prende la prima data disponibile presso il centro di lavoro dove è previsto vengano eseguiti. Il lavoro successivo viene pianificato alla fine dell'esecuzione dell'ultimo ordine di lavoro da eseguire in parallelo.

Le quantità lavorate sugli ordini di lavoro in parallelo si intendono suddivise in maniera proporzionale, quindi se ci sono 2 lavorazioni parallele, si presume che lavorino il 50% dei prodotti ciascuna e il calcolo del tempo per lavorarli sarà il 50% della lavorazione totale. È possibile modificare nell'ordine di lavoro la quantità da eseguire, la cui somma dovrà comunque essere sempre il totale da lavorare.

Non c'è quindi bisogno di impostare ciascuno centro di lavoro con capacità 2 oppure con efficienza 200%, in quanto lo stesso centro di lavoro potrebbe essere utilizzato per altre attività non in parallelo, oppure in parallelo con un valore diverso (ad es. 3 lavorazioni in parallelo).

Impostando il check `Lavorazione parallela` si abilita il campo `Centri di lavoro in parallelo` su cui, in base al numero di centri di lavoro scelti, verrà suddivisa la lavorazione. Nel caso in cui venga scelto un solo centro di lavoro, l'effetto sarà che la lavorazione verrà eseguita singolarmente, ma senza essere pianificata in maniera sequenziale con la lavorazione precedente.

Questo modulo aggiunge la vista timeline e il collegamento tra gli ordini di lavoro padri e quelli figli con una freccia visibile a video:

.. image:: ../static/description/timeline_ordini_lavoro.png
    :alt: Timeline ordini di lavoro

Aggiunge il campo data pianificata finale sulla produzione, calcolata dalla massima data pianificata finale sugli ordini di lavoro. Se non sono stati pianificati gli ordini di lavoro, la data finale non è impostata.

.. image:: ../static/description/timeline_produzione.png
    :alt: Timeline produzioni
