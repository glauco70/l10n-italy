# -*- coding: utf-8 -*-
##############################################################################
#
#    Tech Plus l10n it
#    Copyright (C) Tech Plus srl (<http://www.techplus.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

import openerp.exceptions
import openerp.addons.decimal_precision as dp

from openerp.osv import fields
from openerp.osv.orm import Model
from openerp import SUPERUSER_ID
from openerp.tools.translate import _

# STAMP_STATES = [
#     ('available', 'Available'),
#     ('used', 'Used'),
# ]

# class account_stamp(Model):
#     _name = "account.stamp"
#     _description = "Account stamp"
#     _rec_name = 'product_id'

#     def _get_info(self, cr, uid, ids, name, args, context=None):
#         res = {}
#         for o in self.browse(cr, uid, ids, context=context):
#             res[o.id] = {
#                 'state': 'available' if not o.use_invoice_line_id else 'used',
#             }
#         return res

#     _columns = {
#         'product_id': fields.many2one('product.product', string='Product', required=True, readonly=True,
#             states={'available': [('readonly', False)]}),
#         'serial': fields.char('Stamp code', size=128, required=True, readonly=True,
#             states={'available': [('readonly', False)]}),
#         'emission_date': fields.date('Emission date', readonly=True, states={'available': [('readonly', False)]}),
#         'use_invoice_line_id': fields.many2one('account.invoice.line', string='Use invoice line'),
#         'use_invoice_id': fields.related('use_invoice_line_id', 'invoice_id', type='many2one', relation='account.invoice',
#             string='Use invoice', readonly=True),
#         'state': fields.function(_get_info, type='selection', multi='_get_info', string='State', store=True,
#             selection=STAMP_STATES),
#     }

#     _order = 'serial desc'

#     _defaults = {
#         'state': 'available',
#     }

class account_invoice_line(Model):
    _inherit = "account.invoice.line"

    def _get_line_info(self, cr, uid, ids, name, args, context=None):
        res = {}
        for l in self.browse(cr, uid, ids, context=context):
            amount = l.price_subtotal
            if l.invoice_id.type in ('in_invoice', 'out_refund'):
                amount = - l.price_subtotal
            res[l.id] = {
                'absolute_amount_total': amount,
            }
        return res

    _columns = {
        'absolute_amount_total': fields.function(_get_line_info, type='float', multi='_get_line_info', string='Amount',
            digits_compute=dp.get_precision('Account')),
        'period_id': fields.related('invoice_id', 'period_id', type='many2one',relation='account.period',
            string='Period', readonly=True),
    }