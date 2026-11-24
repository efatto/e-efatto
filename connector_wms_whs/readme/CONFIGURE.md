Vedi modulo connector_whs.

Per tecnici: il collegamento alla sorgente dati è configurata nella VM
nel file whsHost.INI nella cartella C:whsDemo2, in cui viene inserito il
DB: OpenERP-WHS_test e l'IP della stessa VM: 192.168.1.141 (valori che
possono cambiare in base alla configurazione locale).

## Lettura dei confezionamenti (packing)

WMS riversa i confezionamenti nella tabella `HOST_PACKING`, una riga per
confezionamento:

| Campo | Tipo | Note |
|---|---|---|
| `PackingId` | int | identificativo del confezionamento |
| `JsonData` | nvarchar(max) | payload JSON descritto sotto |
| `Elaborato` | int | `0` in elaborazione, `1` elaborabile da Odoo, `2` elaborato da Odoo |

Odoo legge le righe con `Elaborato = 1`, crea o aggiorna il confezionamento e
poi imposta la riga a `Elaborato = 2`. Il payload accettato è:

```json
{
  "PackingId": 1,
  "Packages": [
    {
      "SerialCode": "BOX00000001",
      "PackageType": "EURO PALLET",
      "Dimension": {
        "WeightKg": 0.0,
        "WidthCm": 0.0,
        "HeightCm": 0.0,
        "DepthCm": 0.0
      },
      "Contents": [
        {
          "LogisticSN": "SN00000004",
          "ItemId": "C34100005",
          "Lot": "2436",
          "Lot2": "",
          "Lot3": "9796",
          "Qty": 1.0,
          "OrderNumber": "M-176081",
          "RowNumber": "821965"
        }
      ]
    }
  ]
}
```

`PackageType` e le misure sono testi/valori liberi inseriti dall'operatore WMS
(tipo collo e dimensioni reali). Il prodotto della riga viene collegato tramite
il codice articolo (`ItemId`); se il codice non esiste in Odoo la riga viene
comunque importata senza prodotto.

La lettura può essere lanciata dal pulsante `Read Packages from WMS` sulla
sorgente dati o dal cron `Connector WMS - read packings from WMS`, disattivato
di default: attivarlo quando la tabella `HOST_PACKING` è presente in WMS. Se la
tabella non esiste la lettura viene solo registrata nei log, senza bloccare il
cron.
