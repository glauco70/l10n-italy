# -*- coding: utf-8 -*-
##############################################################################
#
#    Italian Localization - Account Stamp
#    See __openerp__.py file for copyright and licensing details.
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
        'stamp_apply_tax_ids': fields.many2many(
            'account.tax',
            'product_tax_account_tax__rel',
            'product_id', 'tax_id', string='Stamp taxes'),
        'stamp_apply_min_total_base': fields.float(
            'Stamp apply min total base',
            digits_compute=dp.get_precision('Account')),
        'is_stamp': fields.boolean('Is stamp'),
    }

    _constraints = [(
        _check_stamp_apply_tax,
        'The product must be a stamp to set apply taxes!',
        ['stamp_apply_tax_ids', 'is_stamp']
    )]
