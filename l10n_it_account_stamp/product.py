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

import openerp.exceptions
import openerp.addons.decimal_precision as dp

from openerp.osv import fields
from openerp.osv.orm import Model
from openerp.tools.translate import _

class product_template(Model):
    _inherit = 'product.template'

    def _check_stamp_apply_tax(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context):
            if obj.stamp_apply_tax_code_ids and not obj.is_stamp:
                return False
        return True

    _columns = {
        'stamp_apply_tax_code_ids': fields.many2many('account.tax.code', 'product_stamp_account_tax_code_rel', 'product_id',
            'tax_code_id', string='Stamp tax codes'),
        'stamp_apply_min_total_base': fields.float('Stamp apply min total base',
            digits_compute=dp.get_precision('Account')),
        'is_stamp': fields.boolean('Is stamp'),
    }

    _constraints = [
        (_check_stamp_apply_tax, 'The product must be a stamp to set apply taxes!',
            ['stamp_apply_tax_code_ids', 'is_stamp']),
    ]