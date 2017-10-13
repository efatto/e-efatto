# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models, api, exceptions, _
from ..bindings.invoice_statement_v_2_0 import (
    AltriDatiIdentificativiNoCAPType,
    AltriDatiIdentificativiNoSedeType,
    CaricaType,
    CedentePrestatoreDTEType,
    CedentePrestatoreDTRType,
    CessionarioCommittenteDTEType,
    CessionarioCommittenteDTRType,
    DatiFattura,
    DatiFatturaBodyDTEType,
    DatiFatturaBodyDTRType,
    DatiFatturaHeaderType,
    DatiFatturaType,
    DatiGeneraliType,
    DatiGeneraliDTRType,
    DatiIVAType,
    DatiRiepilogoType,
    DichiaranteType,
    DTEType,
    DTRType,
    IdentificativiFiscaliType,
    IdentificativiFiscaliITType,
    IdentificativiFiscaliNoIVAType,
    IdFiscaleITType,
    IdFiscaleType,
    IndirizzoNoCAPType,
    IndirizzoType,
    TipoDocumentoType,
)
import base64
import logging
_logger = logging.getLogger(__name__)

try:
    from unidecode import unidecode
    from pyxb.exceptions_ import SimpleFacetValueError, SimpleTypeValueError
except ImportError as err:
    _logger.debug(err)

import datetime
import re
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


class WizardInvoiceStatement(models.TransientModel):
    _name = "wizard.invoice.statement"
    _description = "Export invoice statement"

    def __init__(self, pool, cr):
        self.statement = False
        super(WizardInvoiceStatement, self).__init__(pool, cr)

    def get_date_start_stop(self, statement):
        date_start = False
        date_stop = False
        for period in statement.period_ids:
            if not date_start:
                date_start = period.date_start
            else:
                if period.date_start < date_start:
                    date_start = period.date_start
            if not date_stop:
                date_stop = period.date_stop
            else:
                if period.date_stop > date_stop:
                    date_stop = period.date_stop
        date_start = datetime.datetime.strptime(date_start,
                                                DEFAULT_SERVER_DATE_FORMAT)
        date_stop = datetime.datetime.strptime(date_stop,
                                               DEFAULT_SERVER_DATE_FORMAT)
        return date_start, date_stop

    def saveAttachment(self, sender_fiscalcode, statement_id):
        attach_obj = self.env['invoice.statement.attachment']
        xml = self.statement.toDOM().toprettyxml(
            encoding="latin1")
        attach_vals = {
            'name': 'IT%s_DF_%s.xml' % (sender_fiscalcode, str(
                statement_id.progressive_number)),
            'datas_fname': 'IT%s_DF_%s.xml' % (sender_fiscalcode, str(
                statement_id.progressive_number)),
            'datas': base64.encodestring(xml),
            'res_model': 'invoice.statement',
            'res_id': statement_id.id,
        }
        attach_id = attach_obj.create(attach_vals)

        return attach_id

    def setCedPrestDTECesComDTR(self, obj, partner_id):
        if partner_id.vat[:2].upper() != 'IT':
            raise exceptions.ValidationError(
                _('No partner != IT allowed'))
        if not partner_id.vat and not partner_id.fiscalcode:
            raise exceptions.ValidationError(
                _('Partner VAT and Fiscalcode not set.'))
        obj.IdentificativiFiscali = (IdentificativiFiscaliITType())
        obj.IdentificativiFiscali.IdFiscaleIVA = (IdFiscaleITType(
            IdPaese=partner_id.vat[:2].upper(), IdCodice=partner_id.vat[2:]
        ))

        obj.AltriDatiIdentificativi = (AltriDatiIdentificativiNoSedeType())
        # get partner name in case of natural person
        if partner_id.individual:
            obj.AltriDatiIdentificativi.Nome = partner_id.first_name
            obj.AltriDatiIdentificativi.Cognome = partner_id.last_name
        else:
            obj.AltriDatiIdentificativi.Denominazione = partner_id.name

        obj.AltriDatiIdentificativi.Sede = (IndirizzoType())
        obj.AltriDatiIdentificativi.Sede.Indirizzo = \
            partner_id.street + (
                ' ' + partner_id.street2 if partner_id.street2 else '')
        if re.match('^[0-9]{5}$', partner_id.zip):
            obj.AltriDatiIdentificativi.Sede.CAP = partner_id.zip
        else:
            raise exceptions.ValidationError(
                'Malformed zip for %s' % partner_id.name)
        obj.AltriDatiIdentificativi.Sede.Comune = partner_id.city
        if partner_id.state_id:
            obj.AltriDatiIdentificativi.Sede.Provincia = partner_id.state_id.\
                code
        obj.AltriDatiIdentificativi.Sede.Nazione = partner_id.country_id.code\
            if partner_id.country_id else 'IT'

    def setCedPrestDTRCesComDTE(
            self, obj, id_fiscali, partner_id, year, statement_id):
        partner_vat = country = False
        if year == 2017 and statement_id.type == 'DTR' and not partner_id.vat:
            partner_vat = '9'*11
            country = 'OO'
        elif not partner_id.vat and not partner_id.fiscalcode:
            raise exceptions.ValidationError(
                _('Partner VAT and Fiscalcode not set.'))
        else:
            partner_vat = partner_id.vat[2:]
            country = partner_id.vat.replace(" ","")[:2].upper()
        obj.IdentificativiFiscali = (id_fiscali)
        obj.IdentificativiFiscali.IdFiscaleIVA = (
            IdFiscaleType(
                IdPaese=country, IdCodice=partner_vat))
        fiscalcode = False
        if partner_id.fiscalcode and (
                partner_id.country_id.code == 'IT' or
                country == 'IT'):
            if len(partner_id.fiscalcode) == 16:
                fiscalcode = partner_id.fiscalcode
            if len(partner_id.fiscalcode) == 13:
                fiscalcode = partner_id.fiscalcode[2:]
        if fiscalcode:
            obj.IdentificativiFiscali.CodiceFiscale = fiscalcode

        obj.AltriDatiIdentificativi = (AltriDatiIdentificativiNoCAPType())
        # get partner name in case of natural person
        if partner_id.individual:
            obj.AltriDatiIdentificativi.Nome = partner_id.first_name
            obj.AltriDatiIdentificativi.Cognome = partner_id.last_name
        else:
            obj.AltriDatiIdentificativi.Denominazione = partner_id.name

        obj.AltriDatiIdentificativi.Sede = (IndirizzoNoCAPType())
        obj.AltriDatiIdentificativi.Sede.Indirizzo = \
            partner_id.street + (
                ' ' + partner_id.street2 if partner_id.street2 else '')
        if partner_id.zip and re.match(
                '^[0-9]{5}$', partner_id.zip) and country == 'IT':
            obj.AltriDatiIdentificativi.Sede.CAP = partner_id.zip
        obj.AltriDatiIdentificativi.Sede.Comune = partner_id.city
        if partner_id.state_id and country == 'IT':
            obj.AltriDatiIdentificativi.Sede.Provincia = partner_id.state_id.\
                code
        obj.AltriDatiIdentificativi.Sede.Nazione = partner_id.country_id.code\
            if partner_id.country_id else country

        return obj

    def get_dati_riepilogo(self, invoice, invoice_tax):
        DatiRiepilogo = False
        if invoice_tax.tax_code_id and not invoice_tax.tax_code_id.\
                exclude_from_registries:
            tax_id = invoice_tax.tax_code_id.tax_ids[0]
            # if tax_id is a child of other tax, use it for aliquota
            if tax_id.parent_id and tax_id.parent_id.child_depend:
                tax_id = tax_id.parent_id
            DatiRiepilogo = DatiRiepilogoType()
            if tax_id.kind_id:
                DatiRiepilogo.Natura = tax_id.kind_id.code
            DatiRiepilogo.ImponibileImporto = '%.2f' % invoice_tax.base
            DatiRiepilogo.DatiIVA = (DatiIVAType())
            DatiRiepilogo.DatiIVA.Imposta = '%.2f' % invoice_tax.amount
            DatiRiepilogo.DatiIVA.Aliquota = '%.2f' % (tax_id.amount * 100)
            # DatiRiepilogo.Natura = se non iva
            esigibilita_iva = 'I'
            if tax_id.payability:
                esigibilita_iva = tax_id.payability
            DatiRiepilogo.EsigibilitaIVA = esigibilita_iva
        else:
            if invoice_tax.base_code_id and not invoice_tax.base_code_id.\
                    exclude_from_registries:
                tax_id = invoice_tax.base_code_id.base_tax_ids[0]
                DatiRiepilogo = DatiRiepilogoType()
                DatiRiepilogo.ImponibileImporto = '%.2f' % invoice_tax.base
                DatiRiepilogo.DatiIVA = (DatiIVAType())
                DatiRiepilogo.Natura = tax_id.kind_id.code
                # N.B. Imposta and Aliquota will be zero here and it is ok
                DatiRiepilogo.DatiIVA.Imposta = '%.2f' % invoice_tax.amount
                DatiRiepilogo.DatiIVA.Aliquota = '%.2f' % (tax_id.amount * 100)
        return DatiRiepilogo

    def _get_fiscal_document_type(self, invoice):
        res = False
        if invoice.fiscal_document_type_id:
            res = invoice.fiscal_document_type_id.code
        else:
            res = self._find_fiscal_document_type(invoice)
        return res

    @staticmethod
    def _find_fiscal_document_type(invoice):
        res = False
        if invoice.type in ['out_invoice', 'in_invoice']:
            res = 'TD01'  # fattura
        elif invoice.type in ['out_refund', 'in_refund']:
            res = 'TD04'  # nota di credito
        # TD05 nota di debito NOT DEFINED IN ODOO
        # TD07 fattura semplificata NOT DEFINED IN ODOO
        # TD08 nota di credito semplificata NOT DEFINED IN ODOO
        if 'CEE' in invoice.journal_id.name.upper() and \
                invoice.type == 'in_invoice':
            res = 'TD10'  # fattura di acquisto intracomunitario beni
            service_amount = sum(
                x.price_subtotal for x in invoice.invoice_line if
                x.product_id.type == 'service')
            product_amount = sum(
                x.price_subtotal for x in invoice.invoice_line if
                x.product_id.type in ['consu', 'product'])
            if service_amount > product_amount:
                res = 'TD11'  # fattura di acquisto intracomunitario servizi
        return res

    @api.multi
    def export_invoice_statement(self):
        invoice_statement_obj = self.env['invoice.statement']
        statement_id = invoice_statement_obj.browse(
            self._context.get('active_id', False))

        # Check sender fiscalcode
        sender_fiscalcode = statement_id.sender_partner_id.fiscalcode
        if len(sender_fiscalcode) == 13:
            if sender_fiscalcode[:2].upper() == 'IT':
                sender_fiscalcode = sender_fiscalcode[2:]
        elif len(sender_fiscalcode) != 16 and len(sender_fiscalcode) != 11:
            raise exceptions.ValidationError('Sender fiscalcode invalid')

        # get data for statement
        date_start, date_stop = self.get_date_start_stop(statement_id)
        progressive_number = invoice_statement_obj.search(
            [], order='progressive_number desc', limit=1).progressive_number

        # create container object Statement
        self.statement = DatiFattura(versione='DAT20') #(DatiFatturaType())
        self.statement.DatiFatturaHeader = (DatiFatturaHeaderType())
        self.statement.DatiFatturaHeader.ProgressivoInvio = str(
            progressive_number + 1)

        # check and put if there is Dichiarante
        if statement_id.statement_partner_id:
            self.statement.DatiFatturaHeader.Dichiarante = (
                DichiaranteType(
                    CodiceFiscale=statement_id.statement_partner_id.fiscalcode,
                    Carica=statement_id.statement_partner_id.codice_carica.code,
                )
            )

        # Get invoices for all cases to remove auto invoices
        DTR_invoice_ids = self.env['account.invoice'].search([
            ('registration_date', '>=', date_start),
            ('registration_date', '<=', date_stop),
            ('type', 'in', ['in_invoice', 'in_refund'],),
            ('state', 'in', ['open', 'paid']),
            '|', ('fiscal_document_type_code', '!=', 'NONE'),
            ('fiscal_document_type_id', '=', False),
        ])
        DTE_invoice_ids = self.env['account.invoice'].search([
            ('registration_date', '>=', date_start),
            ('registration_date', '<=', date_stop),
            ('type', 'in', ['out_invoice', 'out_refund']),
            ('state', 'in', ['open', 'paid']),
            '|', ('fiscal_document_type_code', '!=', 'NONE'),
            ('fiscal_document_type_id', '=', False),
        ])
        auto_invoice_ids = DTR_invoice_ids.filtered('auto_invoice_id')
        DTE_invoice_ids -= auto_invoice_ids.mapped('auto_invoice_id')

        if statement_id.type == 'DTR':
            invoice_ids = DTR_invoice_ids
        elif statement_id.type == 'DTE':
            invoice_ids = DTE_invoice_ids

        # DTR - INVOICE RECEIVED
        if statement_id.type == 'DTR':
            # todo group invoices by partner (limit 1000)
            partner_ids = invoice_ids.mapped('partner_id')
            if partner_ids:
                # CREATE CESSIONARIO - COMMITTENTE DTR
                self.statement.DTR = (DTRType())

                # INSERIRE I DATI DEL MITTENTE - 1 BLOCCO SINGOLO
                self.statement.DTR.CessionarioCommittenteDTR = (
                    CessionarioCommittenteDTRType())
                self.setCedPrestDTECesComDTR(
                    self.statement.DTR.CessionarioCommittenteDTR,
                    statement_id.company_id.partner_id)

            for partner_id in partner_ids:
                # qui si creano piu blocchi, uno per ogni partner
                CedentePrestatoreDTR = self.setCedPrestDTRCesComDTE(
                    CedentePrestatoreDTRType(),
                    IdentificativiFiscaliType(),
                    partner_id, date_stop.year, statement_id,)
                for invoice in invoice_ids.filtered(
                        lambda x: x.partner_id == partner_id):
                    # set invoice body
                    DatiFatturaBodyDTR = DatiFatturaBodyDTRType()
                    DatiFatturaBodyDTR.DatiGenerali = (
                        DatiGeneraliDTRType(
                            TipoDocumento=self._get_fiscal_document_type(
                                invoice),
                            Data=invoice.date_invoice,
                            Numero=invoice.supplier_invoice_number,
                            DataRegistrazione=invoice.registration_date))
                    # SET lines - tax with child and without child
                    for invoice_tax in invoice.tax_line:
                        DatiRiepilogo = self.get_dati_riepilogo(
                            invoice, invoice_tax)
                        if DatiRiepilogo:
                            DatiFatturaBodyDTR.DatiRiepilogo.append(
                                DatiRiepilogo)
                    CedentePrestatoreDTR.DatiFatturaBodyDTR.append(
                        DatiFatturaBodyDTR)
                self.statement.DTR.CedentePrestatoreDTR.append(
                    CedentePrestatoreDTR)

        # DTE - INVOICE EMITTED
        if statement_id.type == 'DTE':
            # todo group invoices by partner (limit 1000)
            partner_ids = invoice_ids.mapped('partner_id')
            if len(partner_ids) > 1000:
                raise exceptions.ValidationError('TODO more than 1000 partner')
            if partner_ids:
                # CREATE CEDENTE - PRESTATORE DTE
                self.statement.DTE = (DTEType())
                # INSERIRE I DATI DEL CEDENTE - 1 BLOCCO SINGOLO
                self.statement.DTE.CedentePrestatoreDTE = (
                    CedentePrestatoreDTEType())
                self.setCedPrestDTECesComDTR(
                    self.statement.DTE.CedentePrestatoreDTE,
                    statement_id.company_id.partner_id)

            for partner_id in partner_ids:
                # qui si creano piu blocchi, uno per ogni partner
                CessionarioCommittenteDTE = self.setCedPrestDTRCesComDTE(
                    CessionarioCommittenteDTEType(),
                    IdentificativiFiscaliNoIVAType(),
                    partner_id, date_stop.year, statement_id,)
                for invoice in invoice_ids.filtered(
                    lambda x: x.partner_id == partner_id):
                    # set invoice body
                    DatiFatturaBodyDTE = DatiFatturaBodyDTEType()
                    DatiFatturaBodyDTE.DatiGenerali = (
                        DatiGeneraliType(
                            TipoDocumento=self._get_fiscal_document_type(
                                invoice),
                            Data=invoice.date_invoice,
                            Numero=invoice.number))
                    # SET lines - tax with child and without child
                    for invoice_tax in invoice.tax_line:
                        DatiRiepilogo = self.get_dati_riepilogo(
                            invoice, invoice_tax)
                        if DatiRiepilogo:
                            DatiFatturaBodyDTE.DatiRiepilogo.append(
                                DatiRiepilogo)
                    CessionarioCommittenteDTE.DatiFatturaBodyDTE.append(
                        DatiFatturaBodyDTE)
                self.statement.DTE.CessionarioCommittenteDTE.append(
                    CessionarioCommittenteDTE)

        statement_id.write(
            {'progressive_number': progressive_number + 1})
        try:
            attach_id = self.saveAttachment(sender_fiscalcode, statement_id)
        except (SimpleFacetValueError, SimpleTypeValueError) as e:
            raise exceptions.ValidationError(
                _("XML SDI validation error"),
                (unicode(e)))
        if statement_id.type == 'DTR':
            val = 'dtr_attachment_id'
        if statement_id.type == 'DTE':
            val = 'dte_attachment_id'
        statement_id.write({val: attach_id.id})
        view_rec = self.env['ir.model.data'].get_object_reference(
            'l10n_it_account_invoice_statement',
            'view_invoice_statement_attachment_form')
        if view_rec:
            view_id = view_rec and view_rec[1] or False
        return {
            'view_type': 'form',
            'name': "Export Invoice Statement",
            'view_id': [view_id],
            'res_id': attach_id.id,
            'view_mode': 'form',
            'res_model': 'invoice.statement.attachment',
            'type': 'ir.actions.act_window',
            'context': self._context,
        }
