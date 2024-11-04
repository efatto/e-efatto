Nel lead è reso disponibile un campo calcolato con il numero dei giorni all'invio della prima offerta, per valutare la velocità di risposta dell'azienda.

I giorni sono calcolati tramite i messaggi a partire dalla data di invio del preventivo, calcolata da:

#. la data di invio della mail standard per l'invio dei preventivi, oppure:
#. la data del primo messaggio di tipo `Ordine inviato`, oppure:
#. la data del primo messaggio che nell'oggetto contiene `Preventivo`, oppure:
#. la data del primo messaggio di tipo `Ordine confermato`.

La data di creazione del lead viene detratta dalLa minore di queste date. La differenza minima viene impostata ad 1 giorno per poter distinguere un preventivo inviato nella stessa data di creazione del lead dai preventivi non inviati o non presenti.

.. image:: ../static/description/giorni_primo_preventivo.png
    :alt: Giorni primo preventivo
