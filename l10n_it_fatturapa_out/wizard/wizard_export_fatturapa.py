# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Davide Corio <davide.corio@lsweb.it>
#    Copyright (C) 2015 Lorenzo Battistini <lorenzo.battistini@agilebg.com>
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
##############################################################################

import base64
import logging
import phonenumbers
from openerp.osv import orm
from openerp.osv import fields
from openerp.osv.orm import except_orm as UserError
from openerp.addons.l10n_it_fatturapa.bindings.fatturapa_v_1_2 import (
    IdFiscaleType,
    ContattiTrasmittenteType,
    CedentePrestatoreType,
    AnagraficaType,
    IndirizzoType,
    IscrizioneREAType,
    CessionarioCommittenteType,
    RappresentanteFiscaleType,
    DatiAnagraficiCedenteType,
    DatiAnagraficiCessionarioType,
    DatiAnagraficiRappresentanteType,
    TerzoIntermediarioSoggettoEmittenteType,
    DatiAnagraficiTerzoIntermediarioType,
    FatturaElettronicaBodyType,
    DatiGeneraliType,
    DettaglioLineeType,
    DatiBeniServiziType,
    DatiRiepilogoType,
    DatiGeneraliDocumentoType,
    DatiDocumentiCorrelatiType,
    ContattiType,
    DatiPagamentoType,
    DettaglioPagamentoType,
    AllegatiType,
    ScontoMaggiorazioneType,
    CodiceArticoloType,
    FatturaElettronica,
    FatturaElettronicaHeaderType,
    DatiTrasmissioneType
)
from openerp.addons.l10n_it_fatturapa.models.account import (
    RELATED_DOCUMENT_TYPES)
from openerp.tools.translate import _
_logger = logging.getLogger(__name__)

try:
    from unidecode import unidecode
    from pyxb.exceptions_ import SimpleFacetValueError, SimpleTypeValueError
except ImportError as err:
    _logger.debug(err)

class WizardExportFatturapa(orm.TransientModel):
    _name = "wizard.export.fatturapa"
    _description = "Export E-invoice"

    def __init__(self, cr, uid, **kwargs):
        fatturapa = False
        self.number = False
        super(WizardExportFatturapa, self).__init__(cr, uid, **kwargs)

    def _domain_ir_values(self, cr, uid, context={}):
        return [('model', '=', context.get('active_model', False)),
                ('key2', '=', 'client_print_multi')]

    _columns = {
        'report_print_menu': fields.many2one('ir.values',
            #domain=_domain_ir_values,
            help='This report will be automatically included in the created XML')
        
        }

    def saveAttachment(self, cr, uid, fatturapa, number, context=None):
        if context is None:
            context = {}

        user_obj = self.pool['res.users']
        company = user_obj.browse(cr, uid, uid).company_id

        if not company.vat:
            raise orm.except_orm(
                _('Error!'), _('Company TIN not set.'))
        if company.fatturapa_sender_partner and not company.fatturapa_sender_partner.vat:
            raise orm.except_orm(_('Error!'), _('Partner %s TIN not set.') % company.fatturapa_sender_partner.name)
        vat = company.vat
        if company.fatturapa_sender_partner:
            vat = company.fatturapa_sender_partner.vat
        vat = vat.replace(' ', '').replace('.', '').replace('-', '')
        attach_obj = self.pool['fatturapa.attachment.out']
        attach_vals = {
            'name': '%s_%s.xml' % (vat, str(number)),
            'datas_fname': '%s_%s.xml' % (vat, str(number)),
            'datas': base64.encodestring(fatturapa.toxml("latin1")),
        }
        attach_id = attach_obj.create(cr, uid, attach_vals, context=context)

        return attach_id

    def setProgressivoInvio(self, cr, uid, fatturapa, context=None):
        if context is None:
            context = {}

        user_obj = self.pool['res.users']
        company = user_obj.browse(cr, uid, uid).company_id
        sequence_obj = self.pool['ir.sequence']
        fatturapa_sequence = company.fatturapa_sequence_id

        if not fatturapa_sequence:
            raise orm.except_orm(
                _('Error!'), _('E-invoice sequence not configured.'))

        number = sequence_obj.next_by_id(
            cr, uid, fatturapa_sequence.id, context=context)

        try:
            fatturapa.FatturaElettronicaHeader.DatiTrasmissione.\
                ProgressivoInvio = number
        except (SimpleFacetValueError, SimpleTypeValueError) as e:
            msg = _(
                'FatturaElettronicaHeader.DatiTrasmissione.'
                'ProgressivoInvio:\n%s'
            ) % unicode(e)
            raise _('Error!'), _(msg)
        return number

    def _setIdTrasmittente(self, cr, uid, company, fatturapa, context=None):
        if context is None:
            context = {}

        if not company.country_id:
            raise orm.except_orm(
                _('Error!'), _('Company Country not set.'))
        IdPaese = company.country_id.code

        IdCodice = company.partner_id.fiscalcode
        if not IdCodice:
            if company.vat:
                IdCodice = company.vat[2:]
        if not IdCodice:
            raise orm.except_orm(
                _('Error'), _('Company does not have fiscal code or VAT'))

        fatturapa.FatturaElettronicaHeader.DatiTrasmissione.\
            IdTrasmittente = IdFiscaleType(
                IdPaese=IdPaese, IdCodice=IdCodice)

        return True

    def _setFormatoTrasmissione(self, cr, uid, partner, fatturapa, company, context=None):
        if context is None:
            context = {}
        
        if partner.is_pa:
            fatturapa.FatturaElettronicaHeader.DatiTrasmissione.\
                FormatoTrasmissione = 'FPA12'
        else:
            fatturapa.FatturaElettronicaHeader.DatiTrasmissione. \
                FormatoTrasmissione = 'FPR12'

        return True

    def _setCodiceDestinatario(self, cr, uid, partner, fatturapa, context=None):
        pec_destinatario = None
        if context is None:
            context = {}
        if partner.is_pa: 
            code = partner.ipa_code
            if not code:
                raise orm.except_orm(
                    _('Error!'), _('IPA Code not set on partner form.'))
        else:
            if not partner.codice_destinatario:
                raise orm.except_orm(_('Error!'), _(
                    "Partner %s is not PA but does not have Codice "
                    "Destinatario"
                ) % partner.name)
            code = partner.codice_destinatario
            if code == '0000000':
                pec_destinatario = partner.pec_destinatario
        fatturapa.FatturaElettronicaHeader.DatiTrasmissione.\
            CodiceDestinatario = code.upper()
        if pec_destinatario:
            fatturapa.FatturaElettronicaHeader.DatiTrasmissione. \
                PECDestinatario = pec_destinatario

        return True

    def _setContattiTrasmittente(self, cr, uid, company, fatturapa, context=None):
        if context is None:
            context = {}

        if not company.phone:
            raise orm.except_orm(
                _('Error!'), _('Company Telephone number not set.'))
        Telefono = self.checkSetupPhone(company.phone)

        if not company.email:
            raise orm.except_orm(
                _('Error!'), _('Email address not set.'))
        Email = company.email
        fatturapa.FatturaElettronicaHeader.DatiTrasmissione.\
            ContattiTrasmittente = ContattiTrasmittenteType(
                Telefono=Telefono, Email=Email)

        return True

    def checkSetupPhone(self, phone_number=False):
        if phone_number and '+' in phone_number:
            phone_number = phonenumbers.format_number(phonenumbers.parse(phone_number), phonenumbers.PhoneNumberFormat.NATIONAL)
        return phone_number

    def setDatiTrasmissione(self, cr, uid, company, partner, fatturapa, context=None):
        if context is None:
            context = {}
        fatturapa.FatturaElettronicaHeader.DatiTrasmissione = (
            DatiTrasmissioneType())
        self._setIdTrasmittente(cr, uid, company, fatturapa, context=context)
        self._setFormatoTrasmissione(cr, uid, partner, fatturapa, company, context=context)
        self._setCodiceDestinatario(cr, uid, partner, fatturapa, context=context)
        self._setContattiTrasmittente(cr, uid, company, fatturapa, context=context)

    def _setDatiAnagraficiCedente(self, cr, uid, CedentePrestatore,
                                  company, context=None):
        if context is None:
            context = {}

        if not company.vat:
            raise orm.except_orm(
                _('Error!'), _('TIN not set.'))
        CedentePrestatore.DatiAnagrafici = DatiAnagraficiCedenteType()
        fatturapa_fp = company.fatturapa_fiscal_position_id
        if not fatturapa_fp:
            raise orm.except_orm(
                _('Error!'), _('FatturaPA fiscal position not set.'))
        CedentePrestatore.DatiAnagrafici.IdFiscaleIVA = IdFiscaleType(
            IdPaese=company.country_id.code, IdCodice=company.vat[2:])
        CedentePrestatore.DatiAnagrafici.Anagrafica = AnagraficaType(
            Denominazione=company.name)

        if company.partner_id.fiscalcode:
            CedentePrestatore.DatiAnagrafici.CodiceFiscale = (
                company.partner_id.fiscalcode)
        CedentePrestatore.DatiAnagrafici.RegimeFiscale = fatturapa_fp.code
        return True

    def _setAlboProfessionaleCedente(self, cr, uid, CedentePrestatore,
                                     company, context=None):
        if context is None:
            context = {}
        # TODO Albo professionale, for now the main company is considered
        # to be a legal entity and not a single person
        # 1.2.1.4   <AlboProfessionale>
        # 1.2.1.5   <ProvinciaAlbo>
        # 1.2.1.6   <NumeroIscrizioneAlbo>
        # 1.2.1.7   <DataIscrizioneAlbo>
        return True

    def _setSedeCedente(self, cr, uid, CedentePrestatore,
                        company, context=None):
        if context is None:
            context = {}

        if not company.street:
            raise orm.except_orm(
                _('Error!'), _('Street not set.'))
        if not company.zip:
            raise orm.except_orm(
                _('Error!'), _('ZIP not set.'))
        if not company.city:
            raise orm.except_orm(
                _('Error!'), _('City not set.'))
        if not company.country_id:
            raise orm.except_orm(
                _('Error!'), _('Country not set.'))
        # FIXME: manage address number in <NumeroCivico>
        # see https://github.com/OCA/partner-contact/pull/96
        CedentePrestatore.Sede = IndirizzoType(
            Indirizzo=company.street,
            CAP=company.zip,
            Comune=company.city,
            Nazione=company.country_id.code)
        if company.partner_id.province:
            CedentePrestatore.Sede.Provincia = company.partner_id.province.code
        return True

    def _setStabileOrganizzazione(self, cr, uid, CedentePrestatore,
                                  company, context=None):
        if context is None:
            context = {}
        if company.fatturapa_stabile_organizzazione:
            stabile_organizzazione = company.fatturapa_stabile_organizzazione
            if not stabile_organizzazione.street:
                raise orm.except_orm(_('Error!'),
                    _('Street not set for %s') % stabile_organizzazione.name)
            if not stabile_organizzazione.zip:
                raise orm.except_orm(_('Error!'),
                    _('ZIP not set for %s') % stabile_organizzazione.name)
            if not stabile_organizzazione.city:
                raise orm.except_orm(_('Error!'),
                    _('City not set for %s') % stabile_organizzazione.name)
            if not stabile_organizzazione.country_id:
                raise orm.except_orm(_('Error!'),
                    _('Country not set for %s') % stabile_organizzazione.name)
            CedentePrestatore.StabileOrganizzazione = IndirizzoType(
                Indirizzo=stabile_organizzazione.street,
                CAP=stabile_organizzazione.zip,
                Comune=stabile_organizzazione.city,
                Nazione=stabile_organizzazione.country_id.code)
            if stabile_organizzazione.province:
                CedentePrestatore.StabileOrganizzazione.Provincia = (
                    stabile_organizzazione.province.code)
        return True

    def _setRea(self, cr, uid, CedentePrestatore, company, context=None):
        if context is None:
            context = {}

        if company.fatturapa_rea_office and company.fatturapa_rea_number:
            CedentePrestatore.IscrizioneREA = IscrizioneREAType(
                Ufficio=(
                    company.fatturapa_rea_office and
                    company.fatturapa_rea_office.code or None),
                NumeroREA=company.fatturapa_rea_number or None,
                CapitaleSociale=(
                    company.fatturapa_rea_capital and
                    '%.2f' % company.fatturapa_rea_capital or None),
                SocioUnico=(company.fatturapa_rea_partner or None),
                StatoLiquidazione=company.fatturapa_rea_liquidation or None
            )

    def _setContatti(self, cr, uid, CedentePrestatore,
                     company, context=None):
        if context is None:
            context = {}
        CedentePrestatore.Contatti = ContattiType(
            Telefono=self.checkSetupPhone(company.partner_id.phone) or None,
            Fax=self.checkSetupPhone(company.partner_id.fax) or None,
            Email=company.partner_id.email or None
        )

    def _setPubAdministrationRef(self, cr, uid, CedentePrestatore,
                                 company, context=None):
        if context is None:
            context = {}
        if company.fatturapa_pub_administration_ref:
            CedentePrestatore.RiferimentoAmministrazione = (
                company.fatturapa_pub_administration_ref)

    def setCedentePrestatore(self, cr, uid, company, fatturapa, context=None):
        fatturapa.FatturaElettronicaHeader.CedentePrestatore = (
            CedentePrestatoreType())
        self._setDatiAnagraficiCedente(
            cr, uid, fatturapa.FatturaElettronicaHeader.CedentePrestatore,
            company, context=context)
        self._setSedeCedente(
            cr, uid, fatturapa.FatturaElettronicaHeader.CedentePrestatore,
            company, context=context)
        self._setAlboProfessionaleCedente(
            cr, uid, fatturapa.FatturaElettronicaHeader.CedentePrestatore,
            company, context=context)
        self._setStabileOrganizzazione(
            cr, uid, fatturapa.FatturaElettronicaHeader.CedentePrestatore,
            company, context=context)
        # FIXME: add Contacts
        self._setRea(
            cr, uid, fatturapa.FatturaElettronicaHeader.CedentePrestatore,
            company, context=context)
        self._setContatti(
            cr, uid, fatturapa.FatturaElettronicaHeader.CedentePrestatore,
            company, context=context)
        self._setPubAdministrationRef(
            cr, uid, fatturapa.FatturaElettronicaHeader.CedentePrestatore,
            company, context=context)

    def _setDatiAnagraficiCessionario(
            self, cr, uid, partner, fatturapa, context=None):
        if context is None:
            context = {}
        fatturapa.FatturaElettronicaHeader.CessionarioCommittente.\
            DatiAnagrafici = DatiAnagraficiCessionarioType()
        if not partner.vat and not partner.fiscalcode:
            raise orm.except_orm(
                _('Error!'), _('Partner VAT and Fiscalcode not set.'))
        if partner.fiscalcode:
            fatturapa.FatturaElettronicaHeader.CessionarioCommittente.\
                DatiAnagrafici.CodiceFiscale = partner.fiscalcode
        if partner.vat:
            fatturapa.FatturaElettronicaHeader.CessionarioCommittente.\
                DatiAnagrafici.IdFiscaleIVA = IdFiscaleType(
                    IdPaese=partner.vat[0:2], IdCodice=partner.vat[2:])
        if partner.is_company:
            fatturapa.FatturaElettronicaHeader.CessionarioCommittente.\
                DatiAnagrafici.Anagrafica = AnagraficaType(
                    Denominazione=partner.name)
        else:
            if not partner.lastname or not partner.firstname:
                raise orm.except_orm(_('Error!'),
                    _("Partner %s deve avere nome e cognome") % partner.name)
            fatturapa.FatturaElettronicaHeader.CessionarioCommittente.\
                DatiAnagrafici.Anagrafica = AnagraficaType(
                    Cognome=partner.lastname,
                    Nome=partner.firstname
                )
        # not using for now

        # Anagrafica = DatiAnagrafici.find('Anagrafica')
        # Nome = Anagrafica.find('Nome')
        # Cognome = Anagrafica.find('Cognome')
        # Titolo = Anagrafica.find('Titolo')
        # Anagrafica.remove(Nome)
        # Anagrafica.remove(Cognome)
        # Anagrafica.remove(Titolo)

        if partner.eori_code:
            fatturapa.FatturaElettronicaHeader.CessionarioCommittente.\
                DatiAnagrafici.Anagrafica.CodEORI = partner.eori_code

        return True









    def _setDatiAnagraficiRappresentanteFiscale(self, partner, fatturapa):
        fatturapa.FatturaElettronicaHeader.RappresentanteFiscale = (
            RappresentanteFiscaleType())
        fatturapa.FatturaElettronicaHeader.RappresentanteFiscale.\
            DatiAnagrafici = DatiAnagraficiRappresentanteType()
        if not partner.vat and not partner.fiscalcode:
            raise orm.except_orm(
                _('Error!'), _('VAT and Fiscalcode not set for %s') % partner.name)
        if partner.fiscalcode:
            fatturapa.FatturaElettronicaHeader.RappresentanteFiscale.\
                DatiAnagrafici.CodiceFiscale = partner.fiscalcode
        if partner.vat:
            fatturapa.FatturaElettronicaHeader.RappresentanteFiscale.\
                DatiAnagrafici.IdFiscaleIVA = IdFiscaleType(
                    IdPaese=partner.vat[0:2], IdCodice=partner.vat[2:])
        fatturapa.FatturaElettronicaHeader.RappresentanteFiscale.\
            DatiAnagrafici.Anagrafica = AnagraficaType(
                Denominazione=partner.name)
        if partner.eori_code:
            fatturapa.FatturaElettronicaHeader.RappresentanteFiscale.\
                DatiAnagrafici.Anagrafica.CodEORI = partner.eori_code

        return True

    def _setTerzoIntermediarioOSoggettoEmittente(self, partner, fatturapa):
        fatturapa.FatturaElettronicaHeader.\
            TerzoIntermediarioOSoggettoEmittente = (
                TerzoIntermediarioSoggettoEmittenteType()
            )
        fatturapa.FatturaElettronicaHeader.\
            TerzoIntermediarioOSoggettoEmittente.\
            DatiAnagrafici = DatiAnagraficiTerzoIntermediarioType()
        if not partner.vat and not partner.fiscalcode:
            raise orm.except_orm(
                _('Error!'), _('Partner VAT and Fiscalcode not set.'))
        if partner.fiscalcode:
            fatturapa.FatturaElettronicaHeader.\
                TerzoIntermediarioOSoggettoEmittente.\
                DatiAnagrafici.CodiceFiscale = partner.fiscalcode
        if partner.vat:
            fatturapa.FatturaElettronicaHeader.\
                TerzoIntermediarioOSoggettoEmittente.\
                DatiAnagrafici.IdFiscaleIVA = IdFiscaleType(
                    IdPaese=partner.vat[0:2], IdCodice=partner.vat[2:])
        fatturapa.FatturaElettronicaHeader.\
            TerzoIntermediarioOSoggettoEmittente.\
            DatiAnagrafici.Anagrafica = AnagraficaType(
                Denominazione=partner.name)
        if partner.eori_code:
            fatturapa.FatturaElettronicaHeader.\
                TerzoIntermediarioOSoggettoEmittente.\
                DatiAnagrafici.Anagrafica.CodEORI = partner.eori_code
        fatturapa.FatturaElettronicaHeader.SoggettoEmittente = 'TZ'
        return True


    def _setSedeCessionario(self, cr, uid, partner, fatturapa, context=None):
        if context is None:
            context = {}

        if not partner.street:
            raise orm.except_orm(
                _('Error!'), _('Customer street not set.'))
        if not partner.zip:
            raise orm.except_orm(
                _('Error!'), _('Customer ZIP not set.'))
        if not partner.city:
            raise orm.except_orm(
                _('Error!'), _('Customer city not set.'))
        # if not partner.province:
        #     raise orm.except_orm(
        #         _('Error!'), _('Customer province not set.'))
        if not partner.country_id:
            raise orm.except_orm(
                _('Error!'), _('Customer country not set.'))

        # FIXME: manage address number in <NumeroCivico>
        fatturapa.FatturaElettronicaHeader.CessionarioCommittente.Sede = (
            IndirizzoType(
                Indirizzo=partner.street,
                CAP=partner.zip,
                Comune=partner.city,
                Nazione=partner.country_id.code))
        if partner.province:
            fatturapa.FatturaElettronicaHeader.CessionarioCommittente.Sede.\
                Provincia=partner.province.code

        return True

    def setRappresentanteFiscale(
            self, cr, uid, company, fatturapa, context=None):
        if context is None:
            context = {}

        if company.fatturapa_tax_representative:
            self._setDatiAnagraficiRappresentanteFiscale(
                company.fatturapa_tax_representative, fatturapa)
        return True

    def setCessionarioCommittente(self, cr, uid, partner, fatturapa, context=None):
        fatturapa.FatturaElettronicaHeader.CessionarioCommittente = (
            CessionarioCommittenteType())
        self._setDatiAnagraficiCessionario(cr, uid, partner, fatturapa, context=context)
        self._setSedeCessionario(cr, uid, partner, fatturapa, context=context)

    def setTerzoIntermediarioOSoggettoEmittente(
            self, cr, uid, company, fatturapa, context=None):
        if context is None:
            context = {}

        if company.fatturapa_sender_partner:
            self._setTerzoIntermediarioOSoggettoEmittente(
                company.fatturapa_sender_partner, fatturapa)
        return True

    def setSoggettoEmittente(self, cr, uid, context=None):
        if context is None:
            context = {}

        # FIXME: this record is to be checked invoice by invoice
        # so a control is needed to verify that all invoices are
        # of type CC, TZ or internally created by the company

        # SoggettoEmittente.text = 'CC'
        return True

    def setDatiGeneraliDocumento(self, cr, uid, invoice, body, context=None):
        if context is None:
            context = {}

        # TODO DatiSAL

        # TODO DatiDDT

        body.DatiGenerali = DatiGeneraliType()
        if not invoice.number:
            raise orm.except_orm(
                _('Error!'),
                _('Invoice does not have a number.'))

        TipoDocumento = 'TD01'
        if invoice.type == 'out_refund':
            TipoDocumento = 'TD04'
        ImportoTotaleDocumento = invoice.amount_total
        if invoice.split_payment:
            ImportoTotaleDocumento += invoice.amount_sp
        body.DatiGenerali.DatiGeneraliDocumento = DatiGeneraliDocumentoType(
            TipoDocumento=TipoDocumento,
            Divisa=invoice.currency_id.name,
            Data=invoice.date_invoice,
            Numero=invoice.number,
            ImportoTotaleDocumento='%.2f' % ImportoTotaleDocumento)

        # TODO: DatiRitenuta, DatiBollo, DatiCassaPrevidenziale,
        # ScontoMaggiorazione, ImportoTotaleDocumento, Arrotondamento,

        if invoice.comment:
            # max length of Causale is 200
            caus_list = invoice.comment.split('\n')
            for causale in caus_list:
                if not causale:
                    continue
                # Remove non latin chars, but go back to unicode string,
                # as expected by String200LatinType
                causale = causale.encode(
                    'latin', 'ignore').decode('latin')
                body.DatiGenerali.DatiGeneraliDocumento.Causale.append(causale)

        if invoice.company_id.fatturapa_art73:
            body.DatiGenerali.DatiGeneraliDocumento.Art73 = 'SI'

        return True

    def setRelatedDocumentTypes(self, cr, uid, invoice, body,
                                context=None):
        for line in invoice.invoice_line:
            for related_document in line.related_documents:
                doc_type = RELATED_DOCUMENT_TYPES[related_document.type]
                documento = DatiDocumentiCorrelatiType()
                if related_document.name:
                    documento.IdDocumento = related_document.name
                if related_document.lineRef:
                    documento.RiferimentoNumeroLinea.append(line.ftpa_line_number)
                if related_document.date:
                    documento.Data = related_document.date
                if related_document.numitem:
                    documento.NumItem = related_document.numitem
                if related_document.code:
                    documento.CodiceCommessaConvenzione = related_document.code
                if related_document.cup:
                    documento.CodiceCUP = related_document.cup
                if related_document.cig:
                    documento.CodiceCIG = related_document.cig
                getattr(body.DatiGenerali, doc_type).append(documento)
        for related_document in invoice.related_documents:
            doc_type = RELATED_DOCUMENT_TYPES[related_document.type]
            documento = DatiDocumentiCorrelatiType()
            if related_document.name:
                documento.IdDocumento = related_document.name
            if related_document.date:
                documento.Data = related_document.date
            if related_document.numitem:
                documento.NumItem = related_document.numitem
            if related_document.code:
                documento.CodiceCommessaConvenzione = related_document.code
            if related_document.cup:
                documento.CodiceCUP = related_document.cup
            if related_document.cig:
                documento.CodiceCIG = related_document.cig
            getattr(body.DatiGenerali, doc_type).append(documento)
        return True

    def setDatiTrasporto(self, cr, uid, invoice, body, context=None):
        if context is None:
            context = {}

        return True

    def setDatiDDT(self, cr, uid, invoice, body):
        return True

    def _get_prezzo_unitario(self, cr, uid, line):
        res = line.price_unit
        if (
            line.invoice_line_tax_id and
            line.invoice_line_tax_id[0].price_include
        ):
            res = line.price_unit / (
                1 + line.invoice_line_tax_id[0].amount)
        return res

    def setDettaglioLinee(self, cr, uid, invoice, body, context=None):
        if context is None:
            context = {}

        body.DatiBeniServizi = DatiBeniServiziType()
        # TipoCessionePrestazione not handled

        # TODO CodiceArticolo

        line_no = 1
        price_precision = self.pool['decimal.precision'].precision_get(cr, uid, 
            'Product Price')
        uom_precision = self.pool['decimal.precision'].precision_get(cr, uid, 
            'Product Unit of Measure')
        for line in invoice.invoice_line:
            if not line.invoice_line_tax_id:
                raise orm.except_orm(
                    _('Error'),
                    _("Invoice line %s does not have tax") % line.name)
            if len(line.invoice_line_tax_id) > 1:
                raise orm.except_orm(
                    _('Error'),
                    _("Too many taxes for invoice line %s") % line.name)
            aliquota = line.invoice_line_tax_id[0].amount * 100
            AliquotaIVA = '%.2f' % (aliquota)
            prezzo_unitario = self._get_prezzo_unitario(cr, uid, line)
            DettaglioLinea = DettaglioLineeType(
                NumeroLinea=str(line_no),
                Descrizione=line.name.replace('\n', ' '),
                PrezzoUnitario=('%.' + str(
                    price_precision
                ) + 'f') % prezzo_unitario,
                Quantita=('%.' + str(
                    uom_precision
                ) + 'f') % line.quantity,
                UnitaMisura=line.uos_id and (
                    unidecode(line.uos_id.name)) or None,
                PrezzoTotale='%.2f' % line.price_subtotal,
                AliquotaIVA=AliquotaIVA)
            if line.discount:
                ScontoMaggiorazione = ScontoMaggiorazioneType(
                    Tipo='SC',
                    Percentuale='%.2f' % line.discount
                )
                DettaglioLinea.ScontoMaggiorazione.append(ScontoMaggiorazione)
            if aliquota == 0.0:
                if not line.invoice_line_tax_id[0].non_taxable_nature:
                    raise orm.except_orm(
                        _('Error'),
                        _("No 'nature' field for tax %s") %
                        line.invoice_line_tax_id[0].name)
                DettaglioLinea.Natura = line.invoice_line_tax_id[
                    0
                ].non_taxable_nature
            if line.admin_ref:
                DettaglioLinea.RiferimentoAmministrazione = line.admin_ref
            if line.product_id:
                if line.product_id.default_code:
                    CodiceArticolo = CodiceArticoloType(
                        CodiceTipo='ODOO',
                        CodiceValore=line.product_id.default_code
                    )
                    DettaglioLinea.CodiceArticolo.append(CodiceArticolo)
                if line.product_id.ean13:
                    CodiceArticolo = CodiceArticoloType(
                        CodiceTipo='EAN',
                        CodiceValore=line.product_id.barcode
                    )
                    DettaglioLinea.CodiceArticolo.append(CodiceArticolo)
            line_no += 1

            body.DatiBeniServizi.DettaglioLinee.append(DettaglioLinea)

        return True

    def setDatiRiepilogo(self, cr, uid, invoice, body, context=None):
        if context is None:
            context = {}
        tax_pool = self.pool['account.tax']
        for tax_line in invoice.tax_line:
            tax_id = self.pool['account.tax'].get_tax_by_invoice_tax(
                cr, uid, tax_line.name, context=context)
            tax = tax_pool.browse(cr, uid, tax_id, context=context)
            riepilogo = DatiRiepilogoType(
                AliquotaIVA='%.2f' % (tax.amount * 100),
                ImponibileImporto='%.2f' % tax_line.base,
                Imposta='%.2f' % tax_line.amount
            )
            if tax.amount == 0.0:
                if not tax.non_taxable_nature:
                    raise orm.except_orm(
                        _('Error'),
                        _("No 'nature' field for tax %s") % tax.name)
                riepilogo.Natura = tax.non_taxable_nature
                if not tax.law_reference:
                    raise orm.except_orm(
                        _('Error'),
                        _("No 'law reference' field for tax %s") % tax.name)
                riepilogo.RiferimentoNormativo = tax.law_reference
            if tax.payability:
                riepilogo.EsigibilitaIVA = tax.payability
            # TODO

            # el.remove(el.find('SpeseAccessorie'))
            # el.remove(el.find('Arrotondamento'))

            body.DatiBeniServizi.DatiRiepilogo.append(riepilogo)

        return True

    def setDatiPagamento(self, cr, uid, invoice, body, context=None):
        if context is None:
            context = {}
        if invoice.payment_term:
            DatiPagamento = DatiPagamentoType()
            if not invoice.payment_term.fatturapa_pt_id:
                raise orm.except_orm(
                    _('Error'),
                    _('Payment term %s does not have a linked e-invoice '
                      'payment term') % invoice.payment_term.name)
            if not invoice.payment_term.fatturapa_pm_id:
                raise orm.except_orm(
                    _('Error'),
                    _('Payment term %s does not have a linked e-invoice '
                      'payment method') % invoice.payment_term.name)
            DatiPagamento.CondizioniPagamento = (
                invoice.payment_term.fatturapa_pt_id.code)
            move_line_pool = self.pool['account.move.line']
            invoice_pool = self.pool['account.invoice']
            payment_line_ids = invoice_pool.move_line_id_payment_get(
                cr, uid, [invoice.id])
            for move_line_id in payment_line_ids:
                move_line = move_line_pool.browse(
                    cr, uid, move_line_id, context=context)
                ImportoPagamento = '%.2f' % move_line.debit
                DettaglioPagamento = DettaglioPagamentoType(
                    ModalitaPagamento=(
                        invoice.payment_term.fatturapa_pm_id.code),
                    DataScadenzaPagamento=move_line.date_maturity,
                    ImportoPagamento=ImportoPagamento
                    )
                if invoice.partner_bank_id:
                    DettaglioPagamento.IstitutoFinanziario = (
                        invoice.partner_bank_id.bank_name)
                    if invoice.partner_bank_id.acc_number:
                        DettaglioPagamento.IBAN = (
                            ''.join(
                                invoice.partner_bank_id.acc_number.split()
                            )
                        )
                    if invoice.partner_bank_id.bank_bic:
                        DettaglioPagamento.BIC = (
                            invoice.partner_bank_id.bank_bic)
                DatiPagamento.DettaglioPagamento.append(DettaglioPagamento)
            body.DatiPagamento.append(DatiPagamento)
        return True

    def setAttachments(self, cr, uid, invoice, body, context=None):
        if context is None:
            context = {}
        if invoice.fatturapa_doc_attachments:
            for doc_id in invoice.fatturapa_doc_attachments:
                AttachDoc = AllegatiType(
                    NomeAttachment=doc_id.datas_fname,
                    Attachment=doc_id.datas
                )
                body.Allegati.append(AttachDoc)
        return True

    def setFatturaElettronicaHeader(self, cr, uid, company,
                                    partner, fatturapa, context=None):
        if context is None:
            context = {}
        fatturapa.FatturaElettronicaHeader = (
            FatturaElettronicaHeaderType())
        self.setDatiTrasmissione(cr, uid, company, partner, fatturapa, context=context)
        self.setCedentePrestatore(cr, uid, company, fatturapa, context=context)
        self.setRappresentanteFiscale(cr, uid, company, fatturapa, context=context)
        self.setCessionarioCommittente(cr, uid, partner, fatturapa, context=context)
        self.setTerzoIntermediarioOSoggettoEmittente(cr, uid, company, fatturapa, context=context)
        self.setSoggettoEmittente(cr, uid, context=context)

    def setFatturaElettronicaBody(
        self, cr, uid, inv, FatturaElettronicaBody, context=None
    ):
        if context is None:
            context = {}

        self.setDatiGeneraliDocumento(
            cr, uid, inv, FatturaElettronicaBody, context=context)
        self.setRelatedDocumentTypes(cr, uid, inv, FatturaElettronicaBody,
                                     context=context)
        self.setDatiTrasporto(
            cr, uid, inv, FatturaElettronicaBody, context=context)
        self.setDettaglioLinee(
            cr, uid, inv, FatturaElettronicaBody, context=context)
        self.setDatiRiepilogo(
            cr, uid, inv, FatturaElettronicaBody, context=context)
        self.setDatiPagamento(
            cr, uid, inv, FatturaElettronicaBody, context=context)
        self.setAttachments(
            cr, uid, inv, FatturaElettronicaBody, context=context)

    def getPartnerId(self, cr, uid, invoice_ids, context=None):
        if context is None:
            context = {}

        invoice_model = self.pool['account.invoice']
        partner = False

        invoices = invoice_model.browse(cr, uid, invoice_ids, context=context)

        for invoice in invoices:
            if not partner:
                partner = invoice.partner_id
            if invoice.partner_id != partner:
                raise orm.except_orm(
                    _('Error!'),
                    _('Invoices must belong to the same partner'))

        return partner

    def exportFatturaPA(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        obj = self.browse(cr, uid, ids[0])
        model_data_obj = self.pool['ir.model.data']
        invoice_obj = self.pool['account.invoice']
        attachments = self.pool['fatturapa.attachment.out']
        user_obj = self.pool['res.users']
        attachment_ids = []
        invoice_ids = context.get('active_ids', False)
        partner = self.getPartnerId(cr, uid, invoice_ids, context=context)
        invoices_by_partner = self.group_invoices_by_partner(cr, uid, ids, context)
        for partner_id in invoices_by_partner:
            invoice_ids = invoices_by_partner[partner_id]
            partner = self.getPartnerId(cr, uid, invoice_ids, context=context)
            if partner.is_pa:
                fatturapa = FatturaElettronica(versione='FPA12')
            else:
                fatturapa = FatturaElettronica(versione='FPR12')
            company = user_obj.browse(cr, uid, uid).company_id
            context_partner = context.copy()
            context_partner.update({'lang': partner.lang})
            user_obj = self.pool['res.users']
            try:
                self.setFatturaElettronicaHeader(cr, uid, company,
                                                 partner, fatturapa, context=context_partner)
                for invoice_id in invoice_ids:
                    inv = invoice_obj.browse(
                        cr, uid, invoice_id, context=context_partner)
                    if inv.fatturapa_attachment_out_id:
                        raise orm.except_orm(
                            _("Error"),
                            _("Invoice %s has E-invoice Export File yet") % (
                                inv.number))
                    if obj.report_print_menu:
                        self.generate_attach_report(cr, uid, ids, inv)
                    invoice_body = FatturaElettronicaBodyType()
                    invoice_obj.preventive_checks(cr, uid, inv.id)
                    self.setFatturaElettronicaBody(
                        cr, uid, inv, invoice_body, context=context_partner)
                    fatturapa.FatturaElettronicaBody.append(invoice_body)
                    # TODO DatiVeicoli

                number = self.setProgressivoInvio(cr, uid, fatturapa, context=context)
            except (SimpleFacetValueError, SimpleTypeValueError) as e:
                raise orm.except_orm(
                    _("XML SDI validation error"),
                    (unicode(e)))

            attach_id = self.saveAttachment(cr, uid, fatturapa, number, context=context)
            attachment_ids.append(attach_id)

            for invoice_id in invoice_ids:
                inv = invoice_obj.browse(cr, uid, invoice_id)
                inv.write({'fatturapa_attachment_out_id': attach_id})

        view_rec = model_data_obj.get_object_reference(
            cr, uid, 'l10n_it_fatturapa_out',
            'view_fatturapa_out_attachment_form')
        if view_rec:
            view_id = view_rec and view_rec[1] or False

        action_to_return = {
            'view_type': 'form',
            'name': "Export FatturaPA",
            'res_model': 'fatturapa.attachment.out',
            'type': 'ir.actions.act_window',
            'context': context
        }
        if len(attachment_ids) == 1:
            action_to_return['view_mode'] = 'form'
            action_to_return['res_id'] = attachment_ids[0]
        else:
            action_to_return['view_mode'] = 'tree,form'
            action_to_return['domain'] = [('id', 'in', attachment_ids)]
        return action_to_return

    def generate_attach_report(self, cr, uid, ids, inv):
        obj = self.browse(cr, uid, ids[0])
        action_report_model, action_report_id = (
            obj.report_print_menu.value.split(',')[0],
            int(obj.report_print_menu.value.split(',')[1]))
        action_report = self.pool[action_report_model] \
            .browse(action_report_id)
        report_model = self.pool['report']
        attachment_model = self.pool['ir.attachment']
        # Generate the PDF: if report_action.attachment is set
        # they will be automatically attached to the invoice,
        # otherwise use res to build a new attachment
        res = report_model.get_pdf(cr, uid, 
            inv.ids, action_report.report_name)
        if action_report.attachment:
            # If the report is configured to be attached
            # to the current invoice, just get that from the attachments.
            # Note that in this case the attachment in
            # fatturapa_doc_attachments is exactly the same
            # that is attached to the invoice.
            attachment = report_model._attachment_stored(
                inv, action_report)[inv.id]
        else:
            # Otherwise, create a new attachment to be stored in
            # fatturapa_doc_attachments.
            filename = inv.number
            data_attach = {
                'name': filename,
                'datas': base64.b64encode(res),
                'datas_fname': filename,
                'type': 'binary'
            }
            attachment = attachment_model.create(data_attach)
        inv.write({
            'fatturapa_doc_attachments': [(0, 0, {
                'is_pdf_invoice_print': True,
                'ir_attachment_id': attachment.id,
                'description': _("Attachment generated by "
                                 "Electronic invoice export")})]
        })

    def group_invoices_by_partner(self, cr, uid, ids, context={}):
        invoice_ids = context.get('active_ids', [])
        res = {}
        for invoice in self.pool.get('account.invoice').browse(cr, uid, invoice_ids):
            if invoice.partner_id.id not in res:
                res[invoice.partner_id.id] = []
            res[invoice.partner_id.id].append(invoice.id)
        return res