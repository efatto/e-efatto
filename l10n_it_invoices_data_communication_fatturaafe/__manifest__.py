# Copyright 2020-2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Italian Localization - Comunicazione dati fatture - '
            'E-fattura AFE integrazione',
    'summary': 'Integrazione fatturazione elettronica AFE e Comunicazione dati '
               'fatture (c.d. "nuovo spesometro")',
    'version': '12.0.1.0.0',
    'category': 'Hidden',
    'author': "Sergio Corato",
    'website': 'https://efatto.it',
    'depends': [
        'l10n_it_invoices_data_communication',
        'l10n_it_fatturapa_in',
        'afe_odoo_connector',
    ],
    'data': [
    ],
    'installable': True,
    'auto_install': True,
}
