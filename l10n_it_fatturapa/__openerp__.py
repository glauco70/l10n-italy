# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Davide Corio <davide.corio@lsweb.it>
#    Copyright 2015 Agile Business Group <http://www.agilebg.com>
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
{
    'name': 'Italian Localization - FatturaPA',
    'version': '0.1',
    'category': 'Localization/Italy',
    'summary': 'Electronic invoices',
    'author': 'Davide Corio, Agile Business Group, Innoviu, '
              'Odoo Community Association (OCA)',
    'website': 'http://www.odoo-italia.org',
    'description': """
.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License

Italian Localization - FatturaPA
================================

Base module to handle FatturaPA data.
http://fatturapa.gov.it

See l10n_it_fatturapa_out and l10n_it_fatturapa_in.


Installation
============

This module requires PyXB 1.2.4
http://pyxb.sourceforge.net/


Configuration
=============

 * Edit the FatturaPA fields of the partners (in partner form) who will receive
   (send) the electronic invoices. IPA code is mandatory, EORI code is not.
 * Configure payment terms filling the fatturaPA fields related to payment
   terms and payment methods.
 * Configure taxes about 'Non taxable nature', 'Law reference'
   and 'VAT payability'
 * Configure FatturaPA data in Accounting Configuration. Note that a sequence
   'fatturaPA' is already loaded by the module and selectable.

Credits
=======

Contributors
------------

* Davide Corio <davide.corio@abstract.it>
* Lorenzo Battistini <lorenzo.battistini@agilebg.com>
* Roberto Onnis <roberto.onnis@innoviu.com>
* Alessio Gerace <alessio.gerace@agilebg.com>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
""",
    'license': 'AGPL-3',
    "depends": [
        'account',
        'techplus_l10n_it',  # 'l10n_it_base', region_id > region
                             #  province_id > province, ecc. ecc.
        # 'l10n_it_fiscalcode', integrato in techplus_l10n_it
        'document',
        #'l10n_it_ipa',  integrato in techplus_l10n_it
        #'l10n_it_rea', integrato in techplus_l10n_it
        'base_iban',
        ],

    "data": [
        'data/fatturapa_data.xml',
        'data/welfare.fund.type.csv',
        'views/account_view.xml',
        'views/company_view.xml',
        'views/partner_view.xml',
        'views/account_tax_view.xml',
        'security/ir.model.access.csv',
    ],
    "demo": ['demo/account_invoice_fatturapa.xml'],
    "installable": True,
    'external_dependencies': {
        'python': ['pyxb'],
    }
}
