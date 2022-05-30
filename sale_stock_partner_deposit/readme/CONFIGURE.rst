Nel partner è stata aggiunta l'ubicazione di deposito, che va creata specifica per il partner:

.. image:: ../static/description/ubicazione_partner_deposito.png
    :alt: deposito

crendo e impostando come padre l'ubicazione generica deposito partner:

.. image:: ../static/description/ubicazione_generica_deposito.png
    :alt: ubicazione generica deposito

.. image:: ../static/description/partner.png
    :alt: partner

Va quindi attivata l'opzione per le rotte specifiche sugli ordini di vendita:

.. image:: ../static/description/attivazione_rotte_so.png
    :alt: attivazione rotte ordine di vendita

e va creato il percorso generico per la vendita da conto deposito:

.. image:: ../static/description/percorso_da_deposito.png
    :alt: percorso da deposito

in cui andrà creata la regola come segue:

.. image:: ../static/description/regola_da_deposito_a_clienti.png
    :alt: regola

Questo percorso verrà usato in maniera generica per qualsiasi trasferimento/vendita di questo tipo, in quanto l'ubicazione di prelievo verrà rilevata dal partner.

È necessario creare un tipo di operazione per la consegna dal conto deposito:

.. image:: ../static/description/operazione_consegna_da_deposito.png
    :alt: operazione consegna da deposito

e un tipo di operazione per la consegna al conto deposito:

.. image:: ../static/description/operazione_consegna_a_deposito.png
    :alt: operazione consegna a deposito

con l'ubicazione di destinazione predefinita del deposito generico.

Facendo quindi una vendita con il percorso definito sopra verso un cliente che ha un deposito, il trasferimento partirà dal deposito specifico:

.. image:: ../static/description/percorso_vendita.png
    :alt: percorso vendita

.. image:: ../static/description/trasferimento_vendita.png
    :alt: trasferimento vendita

Dal partner è possibile aprire direttamente lo stock in deposito presso l'ubicazione con il bottone:

.. image:: ../static/description/deposito_partner.png
    :alt: deposito del partner
