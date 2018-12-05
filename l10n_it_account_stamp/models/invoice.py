# -*- coding: utf-8 -*-
##############################################################################
#
#    Italian Localization - Account Stamp
#    See __openerp__.py file for copyright and licensing details.
#
##############################################################################

import time
import openerp.exceptions

from openerp.osv import fields
from openerp.osv.orm import Model

from openerp.tools.translate import _

class account_invoice(Model):
    _inherit = 'account.invoice'

    def compute_stamps(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        product_obj = self.pool.get('product.product')
        invoice_line_obj = self.pool.get('account.invoice.line')
        stamp_obj = self.pool.get('account.stamp')
        invoice_tax_obj = self.pool.get('account.invoice.tax')
        for inv in self.browse(cr, uid, ids):
            taxes = invoice_tax_obj.compute(cr, uid, inv.id, context)
            tax_base_amounts = {}
            for key in taxes.keys():
                tax_base_amounts[key[0]] = tax_base_amounts.get(key[0], 0.0) + taxes[key]['base_amount']
            to_apply_stamp_product_ids = set()
            stamp_product_ids = product_obj.search(cr, uid, [
                    ('is_stamp', '=', True),
                    ('company_id', '=', inv.company_id.id),
                ], context=context)
            invoice_line_to_unlink_ids = [l.id for l in inv.invoice_line if l.product_id and l.product_id.is_stamp]
            invoice_line_obj.unlink(cr, uid, invoice_line_to_unlink_ids, context)
            for stamp in product_obj.browse(cr, uid, stamp_product_ids, context):
                total_tax_base = 0.0
                for tax_code_id in tax_base_amounts.keys():
                    if tax_code_id in [t.id for t in stamp.stamp_apply_tax_code_ids]:
                        total_tax_base += tax_base_amounts[tax_code_id]
                if inv.type in ('in_invoice', 'in_refund'):
                    total_tax_base = total_tax_base * -1.0
                if total_tax_base >= stamp.stamp_apply_min_total_base:
                    to_apply_stamp_product_ids.add(stamp.id)
            for stamp_product in product_obj.browse(cr, uid, list(to_apply_stamp_product_ids), context):
                if inv.type in ('out_invoice', 'out_refund'):
                    stamp_account_id = stamp_product.property_account_income.id
                else:
                    stamp_account_id = stamp_product.property_account_expense.id
                if not stamp_account_id:
                    raise openerp.exceptions.Warning(_('Missing account configuration for %s') % stamp_product.name)
                line_id = invoice_line_obj.create(cr, uid, {
                        'invoice_id': inv.id,
                        'product_id': stamp_product.id,
                        'name': stamp_product.description_sale,
                        'sequence': 99999,
                        'account_id': stamp_account_id,
                        'price_unit': stamp_product.list_price,
                        'quantity': 1,
                        'uos_id': stamp_product.uom_id.id,
                        'invoice_line_tax_id': [(6, 0, [t.id for t in stamp_product.taxes_id])],
                        'account_analytic_id': None,
                    }, context)

    def button_reset_taxes(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        self.compute_stamps(cr, uid, ids, context)
        return super(account_invoice, self).button_reset_taxes(cr, uid, ids, context)

    def action_move_create(self, cr, uid, ids, context=None):
        self.compute_stamps(cr, uid, ids, context)
        res = super(account_invoice,self).action_move_create(cr, uid, ids, context=context)
        return res

class account_invoice_line(Model):
    _inherit = "account.invoice.line"

    _columns = {
        'is_stamp_line': fields.related('product_id', 'is_stamp', type='boolean', relation='product.product',
            string='Is stamp line', readonly=True),
    }