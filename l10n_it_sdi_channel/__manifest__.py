# -*- coding: utf-8 -*-
#
#
#    Copyright (C) 2017-2018 Sergio Corato
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
#
{
    'name': 'SdI channel',
    'version': '10.0.1.0.0',
    'development_status': 'Alfa',
    'category': 'other',
    'author': 'Sergio Corato',
    'maintainers': [],
    'description': 'Add channel to send-receice xml files to SdI.',
    'website': 'https://efatto.it',
    'license': 'AGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sdi_view.xml',
    ],
    'installable': True,
}
