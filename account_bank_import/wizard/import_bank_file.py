# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models, api, exceptions, _
import base64
import cStringIO
import logging
try:
    import unicodecsv
except ImportError:
    unicodecsv = None


class ImportBankFile(models.TransientModel):
    _name = 'import.bank.file'
    _description = 'Import Bank List File'

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename', required=False)
    delimeter = fields.Char('Delimeter', default=',',
                            help='Default delimeter is ","')

    @api.multi
    def action_import(self):
        for wiz in self:
            if not wiz.data:
                raise exceptions.Warning(_("You need to select a file!"))
            file_data = wiz.data
            delimeter = wiz.delimeter or ','
            data = base64.b64decode(file_data)
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
            bank_obj = self.env['res.bank']
            bank_list = bank_obj.search_read([], ['abi','cab'])
            bank_dict = {el['abi']+el['cab']:el['id'] for el in bank_list}

            keys = ['abi', 'cab', 'name', 'street', 'city', 'zip', 'state']
            if not isinstance(keys, list):
                raise exceptions.Warning(_("Not a valid file!"))
            del reader_info[0]
            step = 1
            for i in range(len(reader_info)):
                field = reader_info[i]
                values = dict(zip(keys, field))
                state = self.env['res.country.state'].search(
                    [('code', '=', values['state'])], limit=1).id
                if not bank_dict.has_key(values['abi'] + values['cab']):
                    bank_obj.create({
                        'name': values['name'],
                        'street': values['street'],
                        'city': values['city'],
                        'zip': values['zip'],
                        'abi': values['abi'],
                        'cab': values['cab'],
                        'state': state,
                    })
                else:
                    bank = bank_obj.search([('abi', '=', values['abi']),
                                           ('cab', '=', values['cab'])],
                                           limit=1)
                    bank.write({
                        'name': values['name'],
                        'street': values['street'],
                        'city': values['city'],
                        'zip': values['zip'],
                        'abi': values['abi'],
                        'cab': values['cab'],
                        'state': state,
                    })
                if i * 100.0 / len(reader_info) > step:
                    logging.getLogger(
                        'openerp.addons.account_bank_import').info(
                        'Esecution {0}% '.format(i * 100.0 / len(reader_info)))
                    step += 1
            return
