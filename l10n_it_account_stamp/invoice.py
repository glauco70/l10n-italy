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

import time
import openerp.exceptions
import openerp.addons.decimal_precision as dp

from openerp.osv import fields
from openerp.osv.orm import Model
from datetime import date, datetime

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _

PLAFOND_DATE_REQUIRED_FROM = '2017-03-01'

INVOICE_STATES = [
    ('draft','Draft'),
    ('proforma','Pro-forma'),
    ('proforma2','Pro-forma'),
    ('open','Open'),
    ('paid','Paid'),
    ('cancel','Cancelled'),
]

class account_invoice(Model):
    _inherit = 'account.invoice'

    def _get_invoice_by_tax(self, cr, uid, ids, context=None):
        return self.pool['account.invoice']._get_invoice_tax(
            cr, uid, ids, context=context)

    def _get_invoice_by_line(self, cr, uid, ids, context=None):
        return self.pool['account.invoice']._get_invoice_line(
            cr, uid, ids, context=context)

    def _build_debit_line(self, invoice):
        if not invoice.company_id.sp_account_id:
            raise openerp.exceptions.Warning(_("Please set 'Split Payment Write-off Account' field in accounting configuration"))
        # if len(invoice.tax_line) != 1:
        #     raise openerp.exceptions.Warning(
        #         _("A split payment invoice must have just one invoice tax line!"))
        tax_lines = []
        for line in invoice.tax_line:
            if line.tax_amount > 0:
                tax_lines.append(line)
        if len(tax_lines) != 1:
            raise openerp.exceptions.Warning(_("A split payment invoice must have just one invoice tax line!"))
        if not tax_lines[0].tax_code_id:
            raise openerp.exceptions.Warning(
                _("Cannot find Split Payment Write-Off Tax Code in invoice tax lines!"))
        vals = {
            'name': _('Split Payment Write Off'),
            'partner_id': invoice.partner_id.id,
            'account_id': invoice.company_id.sp_account_id.id,
            'journal_id': invoice.journal_id.id,
            'period_id': invoice.period_id.id,
            'date': invoice.date_invoice,
            'debit': invoice.amount_sp,
            'credit': 0,
            'tax_code_id': tax_lines[0].tax_code_id.id,
            'tax_amount': - invoice.amount_sp,
            }
        if invoice.type == 'out_refund':
            vals['debit'] = 0
            vals['credit'] = invoice.amount_sp
            vals['tax_amount'] = invoice.amount_sp
        return vals

    def _compute_split_payments(self, cr, uid, ids, context=None):
        for invoice in self.browse(cr, uid, ids, context):
            payment_line_ids = invoice.move_line_id_payment_get()
            move_line_pool = self.pool['account.move.line']
            for payment_line in move_line_pool.browse(cr, uid, payment_line_ids, context):
                inv_total = invoice.amount_sp + invoice.amount_total
                if invoice.type == 'out_invoice':
                    payment_line_amount = (
                        invoice.amount_total * payment_line.debit) / inv_total
                    payment_line.write(
                        {'debit': payment_line_amount}, update_check=False)
                elif invoice.type == 'out_refund':
                    payment_line_amount = (
                        invoice.amount_total * payment_line.credit) / inv_total
                    payment_line.write(
                        {'credit': payment_line_amount}, update_check=False)

    def _compute_amounts(self, cr, uid, ids, field_name, arg, context=None):
        amount_res = self.pool['account.invoice']._amount_all(
            cr, uid, ids, field_name, arg, context)
        for invoice in self.browse(cr, uid, ids, context):
            amount_res[invoice.id]['amount_sp'] = 0
            if invoice.fiscal_position.split_payment:
                amount_res[invoice.id]['amount_sp'] = amount_res[invoice.id]['amount_tax']
                amount_res[invoice.id]['amount_tax'] = 0
                amount_res[invoice.id]['amount_total'] = amount_res[invoice.id]['amount_untaxed'] + amount_res[
                    invoice.id]['amount_tax']
        return amount_res

    def _get_accounts_list(self, cr, uid, ids, name, args, context=None):
        res = {}
        for o in self.browse(cr, uid, ids, context=context):
            accounts = set()
            for l in o.invoice_line:
                accounts.add("%s - %s" % (l.account_id.code, l.account_id.name))
            res[o.id] = '\n'.join(list(accounts)[0:3])
        return res

    # def _get_letter_of_intent(self, cr, uid, ids, name, args, context=None):
    #     res = {}
    #     for o in self.browse(cr, uid, ids, context=context):
    #         letter = None
    #         if o.period_id:
    #             for li in o.partner_id.letter_of_intent_ids:
    #                 if li.fiscal_year_id.id == o.period_id.fiscalyear_id.id:
    #                     if li.plafond_limit_exceeded \
    #                         and li.plafond_limit_exceeded_date \
    #                         and datetime.strptime(o.date_invoice,
    #                         DEFAULT_SERVER_DATE_FORMAT) > datetime.strptime(
    #                         li.plafond_limit_exceeded_date,
    #                         DEFAULT_SERVER_DATE_FORMAT):
    #                         pass
    #                     else:
    #                         letter = li.id
    #                         break
    #         res[o.id] = letter
    #     return res

    def _get_bank_accont_ids(self, cr, uid, ids, name, args, context=None):
        res = {}
        for o in self.browse(cr, uid, ids, context=context):
            bank_ids = set()
            if hasattr(o, 'payment_line_ids'):
                for payment in o.payment_line_ids:
                    if hasattr(payment, 'bank_id') and payment.bank_id:
                        bank_ids.add(payment.bank_id.id)
            res[o.id] = list(bank_ids)
        return res

    # TODO WIP: Ermanno 2016-08-27
    def _check_invoice_number(self, cr, uid, ids):
        context = {}
        for invoice in self.browse(cr, uid, ids):
            if invoice.type in ('in_invoice', 'in_refund') and invoice.date_invoice and invoice.supplier_invoice_number:
                year = str(datetime.strptime(invoice.date_invoice, DEFAULT_SERVER_DATE_FORMAT).year)
                # start_date = '%s-01-01' % year
                # end_date = start_date = '%s-12-31' % year
                invoice_ids = self.search(cr, uid, [
                    ('date_invoice', 'ilike', year),
                    ('partner_id', '=', invoice.partner_id.id),
                    ('id', '!=', invoice.id),
                    ('type', 'in', ('in_invoice', 'in_refund')),
                    ('supplier_invoice_number', '!=', False),
                    ], context=context)
                number = ''.join(c for c in invoice.supplier_invoice_number if c.isdigit() or c.isalpha())
                if any(''.join(c for c in i.supplier_invoice_number if c.isdigit() or c.isalpha()) == number \
                    for i in self.browse(cr, uid, invoice_ids, context)):
                    return False
        return True

    def _get_letter_of_intent_info(self, cr, uid, ids, name, args, context=None):
        res = {}
        for o in self.browse(cr, uid, ids, context=context):
            amount_residual = 0.0
            amount_exceeded = 0.0
            if o.letter_of_intent_id:
                amount_residual = o.letter_of_intent_id.plafond_available_amount
                if amount_residual < 0.0:
                    amount_exceeded = amount_residual
            res[o.id] = {
                'letter_of_intent_amount_residual': amount_residual,
                'letter_of_intent_amount_exceeded': amount_exceeded,
            }
        return res

    _columns = {
        'bank_account_ids': fields.function(_get_bank_accont_ids, type='one2many', obj='res.partner.bank',
            string='Bank Accounts'),
        'account_move_date': fields.date('Account Move Date',
            help='If not empty, this date will be used for the account move instead of the invoice date.'), # Da eliminare - risolve un problema di aggiornamento...
        'accounts_list': fields.function(_get_accounts_list, type='text', string='Accounts List'),
        'vat': fields.related('partner_id', 'vat', type='char', string='VAT', readonly=True),
        'fiscal_code': fields.related('partner_id', 'fiscal_code', type='char', string='Fiscal Code', readonly=True),
        'split_payment': fields.boolean('Split Payment'),
        'split_payment_text': fields.text('Split Payment Text'),
        'letter_of_intent_id': fields.many2one('letter.of.intent', string='Letter Of Intent'),
        'letter_of_intent_amount_residual': fields.function(_get_letter_of_intent_info, type='float',
            multi='_get_letter_of_intent_info', string='Letter of intent residual amount'),
        'letter_of_intent_amount_exceeded': fields.function(_get_letter_of_intent_info, type='float',
            multi='_get_letter_of_intent_info', string='Letter of intent exceeded amount'),
        'registration_date':fields.date('Registration Date', states={
                'paid':[('readonly',True)],
                'open':[('readonly',True)],
                'close':[('readonly',True)],
            }, select=True, help="Keep empty to use the current date"),
        'amount_sp': fields.function(_compute_amounts, string='Split Payment',
            digits_compute=dp.get_precision('Account'), store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_by_tax, None, 20),
                'account.invoice.line': (_get_invoice_by_line, [
                    'price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
                }, multi='all'),
        'amount_untaxed': fields.function(_compute_amounts, digits_compute=dp.get_precision('Account'),
            string='Subtotal', track_visibility='always', store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, [
                    'invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_by_tax, None, 20),
                'account.invoice.line': (_get_invoice_by_line, [
                    'price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
            }, multi='all'),
        'amount_tax': fields.function(_compute_amounts, digits_compute=dp.get_precision('Account'),
            string='Tax', store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_by_tax, None, 20),
                'account.invoice.line': (_get_invoice_by_line, [
                    'price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
            },
            multi='all'),
        'amount_total': fields.function(
            _compute_amounts, digits_compute=dp.get_precision('Account'),
            string='Total', store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_by_tax, None, 20),
                'account.invoice.line': (_get_invoice_by_line, [
                    'price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
            }, multi='all'),
        'split_payment': fields.related('fiscal_position', 'split_payment', type='boolean', string='Split Payment'),
        'date_invoice_search': fields.related('date_invoice', type='date', string='Invoice Date Search', readonly=True),
    }

    _constraints = [
        (_check_invoice_number, 'Another invoice having the same number already exists!', ['supplier_invoice_number']),
    ]

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        new_id = super(account_invoice, self).create(cr, uid, vals, context)
        invoice = self.browse(cr, uid, new_id, context)
        # context['raise_exceptions'] = False
        try:
            self.set_valid_letter_of_intent(cr, uid, invoice, context)
        except:
            pass
        return new_id

    def set_valid_letter_of_intent(self, cr, uid, invoice, context=None):
        letter_obj = self.pool.get('letter.of.intent')
        if context is None:
            context = {}
        if not invoice.letter_of_intent_id and invoice.period_id and invoice.date_invoice:
            domain = [
                ('fiscal_year_id', '=', invoice.period_id.fiscalyear_id.id),
                ('date', '<=', invoice.date_invoice),
                ('expiry_date', '>=', invoice.date_invoice),
                ('partner_id', '=', invoice.partner_id.id),
                ('type', '=', 'in' if invoice.type in ('out_invoice', 'out_refund') else 'out'),
            ]
            if invoice.date_invoice >= PLAFOND_DATE_REQUIRED_FROM and 'refund' not in invoice.type:
                domain.append(('plafond_limit_amount', '>=', invoice.amount_untaxed))
            letter_ids = letter_obj.search(cr, uid, domain, context=context)
            for letter in letter_obj.browse(cr, uid, letter_ids, context):
                if not (letter.single_operation and letter.single_operation_invoice_id) and not letter.has_errors:
                    if invoice.date_invoice >= PLAFOND_DATE_REQUIRED_FROM:
                        if not ('refund' not in invoice.type
                            ) and invoice.amount_untaxed > letter.plafond_available_amount:
                            continue
                    invoice.write({'letter_of_intent_id': letter.id})
                    break
            invoice.refresh()
        if invoice.letter_of_intent_id and invoice.letter_of_intent_id.has_errors:
                raise openerp.exceptions.Warning(
                    _('The selected letter [%s] has warnings. Please, unlink this letter from the invoice or resolve ' \
                      'all letter\'s errors in order to proceed.') % invoice.letter_of_intent_id.name)
        if not invoice.letter_of_intent_id and invoice.fiscal_position.letter_of_intent:
            raise openerp.exceptions.Warning(
                _('A valid letter of intent is required for the partner %s! You should add a valid one ' \
                  'for this invoicing period or you can change the invoice fiscal position; '\
                  'remember to refresh the taxes if you will decide to change the fiscal position.' % \
                  invoice.partner_id.name))
        return invoice.letter_of_intent_id.id if invoice.letter_of_intent_id else None

    def go_to_payments(self, cr, uid, ids, context=None):
        if len(ids) != 1:
            raise openerp.exceptions.Warning('Select just an invoice!')
        invoice = self.browse(cr, uid, ids[0], context)
        if invoice.type in ('out_invoice', 'out_refund'):
            view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher',
                'view_vendor_receipt_form')
        else:
            view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher',
                'view_vendor_payment_form')
        form_view = view_ref and view_ref[1] or False
        move_ids = []
        for payment in invoice.payment_ids:
            move_ids.append(payment.move_id.id)
        voucher_ids = self.pool.get('account.voucher').search(cr, uid, [('move_id', 'in', move_ids)], context=context)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.voucher',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'view_id': False,
            'views': [
                (False, 'tree'),
                (form_view, 'form'),
            ],
            'domain': [('id', 'in', voucher_ids)],
            'target': 'current',
        }

    def get_default_split_payment_vals(self, cr, uid, partner_id, context=None):
        sp = False
        text = None
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id,
                context)
            if partner.has_split_payment:
                sp = True
                if not partner.split_payment_text:
                    text = self.pool.get('ir.config_parameter').get_param(cr,
                        uid, 'techplus_l10n_it.split_payment_text')
                else:
                    text = partner.split_payment_text
        return {
            'split_payment': sp,
            'split_payment_text': text,
        }

    # def _get_period(self, cr, uid, date=None, context=None):
    #     period_ids = self.pool.get('account.period').find(cr, uid, dt=date, context=context)
    #     return period_ids[0] if period_ids else None

    # def on_change_fiscal_position(self, cr, uid, ids, fiscal_position, invoice_type, partner_id, letter_of_intent_id,
    #     date_invoice, amount_untaxed, period_id, context=None):
    #     res = {'value': {'letter_of_intent_id': False}}
    #     if not (partner_id and fiscal_position):
    #         return res
    #     fpos_obj = self.pool.get('account.fiscal.position')
    #     fpos = fpos_obj.browse(cr, uid, fiscal_position, context)
    #     if not fpos.letter_of_intent:
    #         return res
    #     if not date_invoice and fpos.letter_of_intent:
    #         res['warning'] = {
    #             'title': _('Warning!'),
    #             'message': _('Please set the date of the invoice to load the letter of intent automatically!'),
    #         }
    #         return res
    #     period_id = self._get_period(cr, uid, date_invoice, context)
    #     if not period_id:
    #         res['warning'] = {
    #             'title': _('Warning!'),
    #             'message': _('No account period found for the invoice date!'),
    #         }
    #         return res
    #     period = self.pool.get('account.period').browse(cr, uid, period_id, context)
    #     letter_obj = self.pool.get('letter.of.intent')

    #     domain = [
    #         ('fiscal_year_id', '=', period.fiscalyear_id.id),
    #         ('date', '<=', date_invoice),
    #         ('expiry_date', '>=', date_invoice),
    #         ('partner_id', '=', partner_id),
    #         ('type', '=', 'in' if invoice_type in ('out_invoice', 'out_refund') else 'out'),
    #     ]
    #     letter_ids = letter_obj.search(cr, uid, domain, context=context)
    #     for letter in letter_obj.browse(cr, uid, letter_ids, context):
    #         if not (letter.single_operation and letter.single_operation_invoice_id) and not letter.has_errors:
    #             if date_invoice >= PLAFOND_DATE_REQUIRED_FROM:
    #                 if not ('refund' not in invoice_type and amount_untaxed <= letter.plafond_available_amount):
    #                     continue
    #             res['value']['letter_of_intent_id'] = letter.id
    #             break
    #     if not res['value']['letter_of_intent_id']:
    #         res['warning'] = {
    #             'title': _('Warning!'),
    #             'message': _('A valid letter of intent is required for the partner! You should add a valid one ' \
    #                          'for this invoicing period or you can change the invoice fiscal position; ' \
    #                          'remember to refresh the taxes if you will decide to change the fiscal position.'),
    #             }
    #     return res

    # def onchange_partner_id(self, cr, uid, ids, type, partner_id,
    #     date_invoice=False, payment_term=False, partner_bank_id=False,
    #     company_id=False):
    #     res = super(account_invoice, self).onchange_partner_id(cr, uid, ids,
    #         type, partner_id, date_invoice, payment_term, partner_bank_id,
    #         company_id)
    #     sp_vals = self.get_default_split_payment_vals(cr, uid, partner_id,
    #         None)
    #     res.setdefault('value', {}).update(sp_vals)
    #     return res

    # def on_change_split_payment_flag(self, cr, uid, ids, split_payment,
    #     partner_id, context):
    #     if split_payment:
    #         partner = self.pool.get('res.partner').browse(cr, uid, partner_id,
    #             context)
    #         if partner.split_payment_text:
    #             text = partner.split_payment_text
    #         else:
    #             text = self.pool.get('ir.config_parameter').get_param(cr,
    #                 uid, 'techplus_l10n_it.split_payment_text')
    #         return {'value': {'split_payment_text': text}}
    #     return {'value': {'split_payment_text': None}}

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
                # key = (val['tax_code_id'], val['base_code_id'], val['account_id'], val['account_analytic_id'])
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
                        'name': _('Stamp duty paid on the original in possession of the issuer, with identification ' \
                                  'number %s.') % stamp_serial,
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
        # account_move_obj = self.pool.get('account.move')
        # for inv in self.browse(cr, uid, ids):
        #     date_invoice=inv.date_invoice
        #     reg_date = inv.registration_date

        #     # aggancio la lettera di intento
        #     if inv.fiscal_position and inv.fiscal_position.letter_of_intent:
        #         valid_letter_id = self.set_valid_letter_of_intent(cr, uid, inv, context)

        #     if not inv.registration_date:
        #         if not inv.date_invoice:
        #             reg_date = time.strftime('%Y-%m-%d')
        #         else : reg_date = inv.date_invoice
        #     if date_invoice and reg_date :
        #         if (date_invoice > reg_date) :
        #             raise openerp.exceptions.Warning(_('The invoice ' \
        #                 'date cannot be later than the date of registration!'))
        #     #periodo
        #     date_start = inv.registration_date or inv.date_invoice \
        #         or time.strftime('%Y-%m-%d')
        #     date_stop = inv.registration_date or inv.date_invoice \
        #         or time.strftime('%Y-%m-%d')

        #     period_ids = self.pool.get('account.period').search(cr, uid,
        #         [('date_start','<=',date_start),('date_stop','>=',date_stop),
        #         ('company_id', '=', inv.company_id.id)])
        #     if period_ids:
        #         period_id = period_ids[0]
        #     vals = {
        #         'period_id':period_id,
        #     }
        #     if inv.type in ('out_invoice', 'out_refund'):
        #         vals['registration_date'] = reg_date
        #     self.write(cr, uid, [inv.id], vals, context)

        #     mov_date = reg_date or inv.date_invoice or time.strftime('%Y-%m-%d')

        #     account_move_obj.write(cr, uid, [inv.move_id.id],
        #         {'state':'draft'})

        #     sql = "update account_move_line set period_id = %d, date = '%s' " \
        #           "where move_id = %d" % (period_id, mov_date, inv.move_id.id)

        #     cr.execute(sql)
        #     vals = {
        #         'period_id':period_id,
        #         'date':mov_date,
        #         'state':'posted',
        #     }

        #     if inv.type in ('in_refund', 'in_invoice') and \
        #         inv.supplier_invoice_number:
        #         vals['ref'] = 'Fatt. %s' % (
        #             inv.supplier_invoice_number)

        #     account_move_obj.write(cr, uid, [inv.move_id.id], vals)

        # self._log_event(cr, uid, ids)

        # for invoice in self.browse(cr, uid, ids, context):
        #     if invoice.fiscal_position and invoice.fiscal_position.split_payment:
        #         if invoice.type in ['in_invoice', 'in_refund']:
        #             raise openerp.exceptions.Warning(
        #                 _("Can't handle supplier invoices with split payment"))
        #         invoice._compute_split_payments()
        #         line_obj = self.pool.get('account.move.line')
        #         write_off_line_vals = self._build_debit_line(invoice)
        #         write_off_line_vals['move_id'] = invoice.move_id.id
        #         line_obj.create(cr, uid, write_off_line_vals, context=context)
        #         # trigger recompute of amount_residual
        #         self.write(cr, uid, ids, {'invoice_line': []}, context=context)

        return res

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        types = {
                'out_invoice': _('Invoice'),
                'in_invoice': _('Supplier Invoice'),
                'out_refund': _('Refund'),
                'in_refund': _('Supplier Refund'),
                }
        res = []
        records = self.read(cr, uid, ids,
            ['type', 'number', 'name', 'supplier_invoice_number'], context,
            load='_classic_write')
        for r in records:
            n = ''
            if r['number']:
                n = r['number']
            if r['supplier_invoice_number']:
                if n:
                    n += ': '
                n += r['supplier_invoice_number']
            if not n:
                n = types[r['type']]
            if r['name']:
                if n:
                    n += ' '
                n += r['name']
            res.append((r['id'], n))
        return res

    def name_search(self, cr, user, name, args=None, operator='ilike',
        context=None, limit=100):
        if not args:
            args = []
        if context is None:
            context = {}
        ids = []
        if name:
            ids = self.search(cr, user, ['|', ('number','=',name),
                ('supplier_invoice_number', 'ilike', name)] + args,
                limit=limit, context=context)
        if not ids:
            ids = self.search(cr, user, ['|', ('name', operator, name),
                ('supplier_invoice_number', 'ilike', name)] + args,
                limit=limit, context=context)
        return self.name_get(cr, user, ids, context)

    def switch_taxes_and_accounts(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for invoice in self.browse(cr, uid, ids, context):
            if not invoice.fiscal_position:
                raise openerp.exceptions.Warning(
                    _('Fiscal position is needed in order to switch taxes!'))
            fpos = invoice.fiscal_position
            tax_lookup = {}
            account_lookup = {}
            # Invoice line update
            for line in fpos.tax_ids:
                tax_lookup[str(line.tax_src_id.id)] = line.tax_dest_id.id
            for line in fpos.account_ids:
                account_lookup[str(line.account_src_id.id)] = line.account_dest_id.id
            for line in invoice.invoice_line:
                line_tax_ids = []
                account_id = line.account_id.id
                for tax in line.invoice_line_tax_id:
                    if tax_lookup.get(str(tax.id)):
                        line_tax_ids.append(tax_lookup.get(str(tax.id)))
                    else:
                        line_tax_ids.append(tax.id)
                if account_lookup.get(str(line.account_id.id)):
                    account_id = account_lookup.get(str(line.account_id.id))
                line.write({
                        'invoice_line_tax_id': [(6, 0, line_tax_ids)],
                        'account_id': account_id,
                    })
            # Invoice journal update
            if invoice.type == 'out_invoice' and fpos.default_sale_journal_id:
                invoice.write({'journal_id': fpos.default_sale_journal_id.id})
            elif invoice.type == 'out_refund' and fpos.default_sale_refund_journal_id:
                invoice.write({'journal_id': fpos.default_sale_refund_journal_id.id})
            elif invoice.type == 'in_invoice' and fpos.default_purchase_journal_id:
                invoice.write({'journal_id': fpos.default_purchase_journal_id.id})
            elif invoice.type == 'in_refund' and fpos.default_purchase_refund_journal_id:
                invoice.write({'journal_id': fpos.default_purchase_refund_journal_id.id})
            # Invoice account update
            # if invoice.partner_id.property_account_receivable == xxx and \
            #    invoice.type in ('out_invoice', 'out_refund'):

        return True

class account_invoice_line(Model):
    _inherit = "account.invoice.line"

    def _get_info(self, cr, uid, ids, name, args, context=None):
        res = {}
        stamp_obj = self.pool.get('account.stamp')
        for o in self.browse(cr, uid, ids, context=context):
            stamp_ids = stamp_obj.search(cr, uid, [
                    ('use_invoice_line_id', '=', o.id),
                ], context=context)
            res[o.id] = {
                'stamp_id': stamp_ids[0] if stamp_ids else False,
            }
        return res

    _columns = {
        'invoice_state': fields.related('invoice_id', 'state', type='selection', selection=INVOICE_STATES,
            string='Invoice State', readonly=True),
        'stamp_id': fields.function(_get_info, type='many2one', obj='account.stamp', multi='_get_info',
            string='Account stamp'),
    }


    def unlink(self, cr, uid, ids, context=None):
        stamp_obj = self.pool.get('account.stamp')
        used_stamp_ids = stamp_obj.search(cr, uid, [('use_invoice_line_id', 'in', ids)], context=context)
        res = super(account_invoice_line, self).unlink(cr, uid, ids, context)
        stamp_obj.write(cr, uid, used_stamp_ids, {}, context)
        return res