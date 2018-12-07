# -*- coding: utf-8 -*-
##############################################################################
#
#    Italian Localization - FatturaPA - Emission - PEC Support
#
#    Author(s): Ermanno Gnan (ermannognan@gmai.com)
#    Copyright © 2018 Sergio Corato (https://efatto.it)
#    Copyright © 2018 Enrico Ganzaroli (enrico.gz@gmail.com)
#    Copyright © 2018 Ermanno Gnan (ermannognan@gmail.com)
#
#    License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
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
    ],
    'data': [
        'data/data.xml',
        'views/invoice_view.xml',
        'views/product_view.xml',
        # 'views/menu.xml',
    ],
    'js': [
    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
}
