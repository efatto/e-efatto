Sulla riga ordine di vendita è presente un'icona a forma di edificio:

.. image:: ../static/description/forecast_icon.png
    :alt: Forecast icon

che se cliccata genera un report pivot con le quantità disponibili per data del prodotto e dei suoi componenti nel caso abbia un distinta base:

.. image:: ../static/description/forecast_pivot.png
    :alt: Forecast pivot

Le quantità sono separate per documento di origine:
 #. da ordine di vendita
 #. da magazzino
 #. da produzione (prodotto)
 #. da produzione (componente)

Ad es. la disponibilità cumulativa al 01/07/2021 è:

.. image:: ../static/description/disponibilita.png
    :alt: Disponibilità

mentre al 23/07/2021 è:

.. image:: ../static/description/disponibilita_maggiore.png
    :alt: Disponibilità maggiore

n.b. la disponibilità di un articolo in arrivo in magazzino il giorno x è calcolata per il giorno x+1
