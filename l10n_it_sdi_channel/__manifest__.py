# -*- coding: utf-8 -*-
# Copyright 2018 Sergio Corato (https://efatto.it)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "SdI channel",
    "summary": "Add channel to send-receice xml files to SdI.",
    "version": "10.0.1.0.0",
    "development_status": "Alpha",
    "category": "other",
    "website": "https://github.com/OCA/l10n-italy",
    "author": "Efatto.it di Sergio Corato, Odoo Community Association (OCA)",
    "maintainers": ["sergiocorato"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/sdi_view.xml",
    ],
}
