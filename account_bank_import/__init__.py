# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from . import wizard
import logging
import os
from openerp import SUPERUSER_ID, exceptions, _
import cStringIO
try:
    import unicodecsv
except ImportError:
    unicodecsv = None


def post_init_hook(cr, registry):
    logging.getLogger('openerp.addons.account_bank_import').info(
        'Importing Italian banks')
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    file_name = 'res.bank.may2016.csv'
    data = open(os.path.join(path, 'data_it', file_name), 'r').read()
    delimeter = ','
    file_input = cStringIO.StringIO(data)
    file_input.seek(0)
    reader_info = []
    reader = unicodecsv.reader(file_input, encoding='utf-8',
                               delimiter=str(delimeter))
    try:
        reader_info.extend(reader)
    except Exception:
        raise exceptions.Warning(_("Not a valid file!"))
    # keys2 = reader_info[0]
    bank_obj = registry['res.bank']
    state_obj = registry['res.country.state']
    bank_list = bank_obj.search_read(cr, SUPERUSER_ID, [], ['abi','cab'])
    bank_dict = {el['abi']+el['cab']: el['id'] for el in bank_list}
    keys = ['abi', 'cab', 'name', 'street', 'city', 'zip', 'state']
    if not isinstance(keys, list):
        raise exceptions.Warning(_("Not a valid file!"))
    del reader_info[0]
    step = 1
    for i in range(len(reader_info)):
        field = reader_info[i]
        values = dict(zip(keys, field))
        if not bank_dict.has_key(values['abi'] + values['cab']):
            state = state_obj.search(cr, SUPERUSER_ID,
                    [('code', '=', values['state'])]) or [False]
            bank_obj.create(cr, SUPERUSER_ID, {
                'name': values['name'],
                'street': values['street'],
                'city': values['city'],
                'zip': values['zip'],
                'abi': values['abi'],
                'cab': values['cab'],
                'state': state[0],
            })
        if i*100.0/len(reader_info) > step:
            logging.getLogger('openerp.addons.account_bank_import').info(
                'Esecution {0}% '.format(i*100.0/len(reader_info)))
            step += 1
    return