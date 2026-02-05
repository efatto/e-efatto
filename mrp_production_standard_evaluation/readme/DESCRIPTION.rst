Questo modulo aggiorna i costi dei prodotti consumati e finiti a seguito delle modifiche fatte dopo il completamento, in parte permesse a seguito dell'installazione del modulo `mrp_production_consume_done`.

Quando una produzione viene sbloccata e vengono modificate possibilmente le quantità consumate dei componenti o le ore registrate negli ordini di lavoro, al successivo blocco vengono ricalcolati i costi.

Questo modulo imposta che i costi vengono assegnati, se non configurata una modalità di valorizzazione nelle categorie dei prodotti, al costo standard dei prodotti quando assegnati alla produzione.

Inoltre questo modulo imposta il costo del prodotto finito pari al costo di produzione registrato nel movimento di carico, in modo da tenerlo sempre aggiornato. Attenzione: se venisse modificata una produzione in una data passata, quel costo andrebbe a sovrascrivere il costo del prodotto, anche se ci fossero delle produzioni posteriori.

Infine questo modulo aggiorna il costo della produzione padre se la produzione che si sta modificando produce un componente della stessa, se la produzione è stata generata dalla produzione padre (quindi non aggiorna una qualsiasi produzione che usi quel componente).

N.B.: Modificando le quantità completate nella produzione, i costi vengono ricalcolati sulla base dei prezzi presenti nei movimenti di magazzino, già assegnati in precedenza.

TODO aggiornare i costi dei componenti al momento dell'avvio della produzione? Oppure quando la produzione è completata? Non quando viene modificata a posteriori, eccetto per le righe modificate.
