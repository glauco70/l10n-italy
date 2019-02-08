# -*- coding: utf-8 -*-
# Copyright 2019 Sergio Corato
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Italian Localization - Fattura elettronica - Management data",
    "summary": "Modulo che permette di gestire il campo AltriDatiGestionali",
    "version": "8.0.1.0.0",
    "development_status": "Beta",
    "category": "Hidden",
    "website": "https://github.com/OCA/l10n-italy",
    "author": "Sergio Corato, Odoo Community Association (OCA)",
    "maintainers": ["sergiocorato"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "l10n_it_fatturapa_out",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/account_view.xml",
    ],
}
