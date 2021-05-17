# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Intrastat Customs Tariff',
    'version': '12.0.1.0.0',
    'author': 'Sergio Corato',
    'category': 'other',
    'depends': [
        'l10n_it_intrastat',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/report_intrastat.xml',
    ],
    'description': "Add Customs Tariff to Intrastat Code",
    'installable': True,
}
