# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from openerp import fields, models, api, _


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    related_mngt_data_ids = fields.One2many(
        'fatturapa.mngt_data_type', 'invoice_id',
        'Related management datas', copy=False
    )


class FatturapaMngtData(models.Model):
    _name = 'fatturapa.mngt_data_type'
    _description = 'FatturaPA Mngt Data Type'

    name = fields.Char('Name', size=10, required=True)
    lineRef = fields.Integer('LineRef')
    invoice_id = fields.Many2one(
        'account.invoice', 'Related Invoice',
        ondelete='cascade', index=True)
    invoice_line_id = fields.Many2one(
        'account.invoice.line', 'Related Invoice Line',
        ondelete='cascade', index=True)
    text_ref = fields.Char('Reference Text', size=60)
    number_ref = fields.Float('Reference Number')
    date_ref = fields.Date('Reference Date')

    @api.model
    def create(self, vals):
        if vals.get('invoice_line_id'):
            line_obj = self.env['account.invoice.line']
            line = line_obj.browse(vals['invoice_line_id'])
            vals['lineRef'] = line.sequence
        return super(FatturapaMngtData, self).create(vals)
