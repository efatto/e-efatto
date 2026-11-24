This is an extension to module connector_whs to connect WMS WHSystem.

It also reads the packings (colli) produced by WMS during the packing
procedure. WMS writes one row per packing in the `HOST_PACKING` table and Odoo
stores it in `WMS Packings` (Inventory > Operations), with the packages
(`hyddemo.whs.package`) and their contents (`hyddemo.whs.package.content`).
