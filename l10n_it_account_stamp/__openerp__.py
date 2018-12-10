# -*- coding: utf-8 -*-
# Author(s): Ermanno Gnan (ermannognan@gmai.com)
# Copyright © 2018 Sergio Corato (https://efatto.it)
# Copyright © 2018 Enrico Ganzaroli (enrico.gz@gmail.com)
# Copyright © 2018 Ermanno Gnan (ermannognan@gmail.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Account Stamp',
    'version': '10.0.0.0.1',
    'category': 'Localisation/Italy',
    'summary': 'Account stamp automatic management',
    'description': """
Account Stamp

Functionalities:

- Adds account stamp support.
- Invoices stamp lines reports: "assolvimento dell’imposta di bollo ai sensi 
dell’articolo 6, comma 2, del Dm 17 giugno 2014".

""",
    'author': 'Ermanno Gnan, Sergio Corato, Enrico Ganzaroli, '
              'Odoo Community Association (OCA)',
    'website': 'https://odoo-community.org',
    'depends': [
        'product',
        'account',
    ],
    'data': [
        'data/data.xml',
        'views/invoice_view.xml',
        'views/product_view.xml',
        'views/company_view.xml',
    ],
    'installable': True,
}
