
Crea un prodotto di tipo consumabile o stoccabile con:

* a value in field 'weight';

.. image:: ../static/description/peso.png
    :alt: Peso prodotto

* set True on field 'compute_price_on_weight';

.. image:: ../static/description/prodotto.png
    :alt: Prodotto

* add a Seller with a price

.. image:: ../static/description/prezzo-fornitore-kg.png
    :alt: Fornitore

Quindi creando un ordine di acquisto con questo prodotto, il prezzo unitario
sarà calcolato con la formula: prezzo fornitore * peso prodotto.

Un campo calcolato 'Peso totale' è mostrato nella riga dell'ordine di acquisto.

.. image:: ../static/description/acquisto.png
    :alt: Ordine di acquisto

In questo modo, con logica di gestione invariata, si ha una soluzione semplice
per gestire i prodotti acquistati a peso ma che vengono gestiti internamente
con una diversa unità di misura.
