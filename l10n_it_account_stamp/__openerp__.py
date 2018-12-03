# -*- coding: utf-8 -*-
##############################################################################
#
#    Tech Plus l10n it
#    Copyright (C) Tech Plus srl (<http://www.techplus.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Account Stamp',
    'version': '0.1',
    'category': 'Localisation/Italy',
    'description': """
OpenERP Account Stamp

Functionalities:

- Adds account stamp support.
- Invoices stamp lines reports: "assolvimento dell’imposta di bollo ai sensi dell’articolo 6, comma 2, del Dm 17 giugno 2014".
- Stamp payment management: lista delle marche da bollo non ancora assolte con giorni rimanenti alla scadenza per l'assoluzione. Le righe fattura con marca da bollo hanno uno stato che sarà "da assolvere" o "assolte".


""",
    'author': 'OCA',
    'website': 'http://www.techplus.it',
    'summary': 'account stamp automatic management',
    'depends': [
        'web',
        'product',
        'account',
        'l10n_it',
    ],
    'data': [
        'data/data.xml',
        # 'security/ir.model.access.csv',
        # 'account_view.xml',
        # 'invoice_view.xml',
        'product_view.xml',
        # 'menu.xml',
    ],
    'js': [
    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
}
