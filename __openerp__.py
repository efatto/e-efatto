# -*- coding: utf-8 -*-
#
#
#    Copyright (C) 2017 Sergio Corato
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
{
    'name': 'Account invoice statement',
    'version': '8.0.1.0.0',
    'category': 'other',
    'author': 'Sergio Corato',
    'description': 'Invoice Statement 2017 export xml file',
    'website': 'http://www.efatto.it',
    'license': 'AGPL-3',
    'depends': [
        'sale',
        'account',
        # 'account_vat_period_end_statement',
        # 'account_vat_statement_endyear',
        # 'l10n_it_vat_registries',
        'l10n_it_fiscalcode',
        'l10n_it_codici_carica',
        'l10n_it_account_tax_kind',
        'l10n_it_esigibilita_iva',
        'l10n_it_fiscal_document_type',
    ],
    'data': [
        'wizard/add_period.xml',
        'wizard/remove_period.xml',
        'views/res_partner.xml',
        'views/invoice_statement.xml',
        'wizard/wizard_invoice_statement.xml',
    ],
    'external_dependencies': {
        'python': ['pyxb'],
    },
    'installable': True
}
