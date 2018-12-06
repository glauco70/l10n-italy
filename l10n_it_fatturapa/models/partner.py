# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Davide Corio <davide.corio@lsweb.it>
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

from openerp.osv import fields, orm
from openerp.osv.osv import except_osv
from openerp.tools.translate import _


class res_partner(orm.Model):
    _inherit = "res.partner"

    _columns = {
        'eori_code': fields.char('EORI Code', size=20),
        'license_number': fields.char('License Code', size=20),
        # 1.2.6 RiferimentoAmministrazione
        'pa_partner_code': fields.char('PA Code for partner', size=20),
        # 1.2.1.4
        'register': fields.char('Professional Register', size=60),
        # 1.2.1.5
        'register_province': fields.many2one(
            'res.province', string='Register Province'),
        # 1.2.1.6
        'register_code': fields.char('Register Code', size=60),
        # 1.2.1.7
        'register_regdate': fields.date('Register Registration Date'),
        # 1.2.1.8
        'register_fiscalpos': fields.many2one(
            'fatturapa.fiscal_position',
            string="Register Fiscal Position"),
        

        'codice_destinatario': fields.char(
            "Codice Destinatario",
            help="Il codice, di 7 caratteri, assegnato dal Sdi ai soggetti che "
             "hanno accreditato un canale; qualora il destinatario non abbia "
             "accreditato un canale presso Sdi e riceva via PEC le fatture, "
             "l'elemento deve essere valorizzato con tutti zeri ('0000000'). "),
        'pec_destinatario' : fields.char(
        "PEC destinatario",
        help="Indirizzo PEC al quale inviare la fattura elettronica. "
             "Da valorizzare "
             "SOLO nei casi in cui l'elemento informativo "
             "<CodiceDestinatario> vale '0000000'"
             ),
        'electronic_invoice_subjected' : fields.boolean(
        "Subjected to electronic invoice"),
    }
    
    _defaults = {
        'codice_destinatario': '0000000',
        }

    def _check_ftpa_partner_data(self, cr, uid, ids, context={}):
        for partner in self.browse(cr, uid, ids):
            if partner.electronic_invoice_subjected:
                if partner.is_pa and (
                    not partner.ipa_code or len(partner.ipa_code) != 6
                ):
                    raise except_osv(_('Error' ),
                             _(
                        "Il partner %s, essendo una pubblica amministrazione "
                        "deve avere il codice IPA lungo 6 caratteri"
                    ) % partner.name)
                if not partner.is_pa and (
                    not partner.codice_destinatario or
                    len(partner.codice_destinatario) != 7
                ):
                    raise except_osv(_('Error' ),_(
                        "Il partner %s "
                        "deve avere il Codice Destinatario lungo 7 caratteri"
                    ) % partner.name)
                if not partner.is_company and (
                    not partner.lastname or not partner.firstname
                ):
                    raise except_osv(_('Error' ),_(
                        "Il partner %s, essendo persona "
                        "deve avere Nome e Cognome"
                    ) % partner.name)
                if (
                    not partner.is_pa and
                    partner.codice_destinatario == '0000000'
                ):
                    if not partner.vat and not partner.fiscalcode:
                        raise except_osv(_('Error' ),_(
                            "Il partner %s, con Codice Destinatario '0000000',"
                            " deve avere o P.IVA o codice fiscale"
                        ) % partner.name)
                if partner.customer:
                    if not partner.street:
                        raise except_osv(_('Error' ),_(
                            'Customer %s: street is needed for XML generation.'
                        ) % partner.name)
                    if not partner.zip:
                        raise except_osv(_('Error' ),_(
                            'Customer %s: ZIP is needed for XML generation.'
                        ) % partner.name)
                    if not partner.city:
                        raise except_osv(_('Error' ),_(
                            'Customer %s: city is needed for XML generation.'
                        ) % partner.name)
                    if not partner.country_id:
                        raise except_osv(_('Error' ),_(
                            'Customer %s: country is needed for XML'
                            ' generation.'
                        ) % partner.name)
        return True

    _constraints = [
        (_check_ftpa_partner_data, 'Some customer infos are needed.', [
            'is_pa', 'ipa_code', 'codice_destinatario', 'company_type',
            'electronic_invoice_subjected', 'vat', 'fiscalcode', 'lastname',
            'firstname', 'customer', 'street', 'zip', 'city',
            'country_id']),
    ]

