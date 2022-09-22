# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'MRP Production BoM Change',
    'version': '12.0.1.0.1',
    'development_status': 'Beta',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'author': 'Sergio Corato Efatto.it',
    'website': 'https://efatto.it',
    'description': 'Change BoM in production.',
    'depends': [
        'mrp_production_demo',
        'mrp_production_lot_custom_assign',  # added for tests
    ],
    'data': [
        'wizard/mrp_production_bom_change.xml',
        'views/mrp.xml',
    ],
    'installable': True,
}
