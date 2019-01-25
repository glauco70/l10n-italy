# -*- coding: utf-8 -*-

from openerp.osv import fields, osv, orm

class ResCompany(orm.Model):
    _inherit = 'res.company'

    _columns = {
        'e_invoice_user_id': fields.many2one(
            "res.users", string="E-invoice creator",
            help="This user will be used at supplier e-invoice creation.",
        ),
    }

    _defaults = {
        'e_invoice_user_id': lambda self, cr, uid, ctx: uid,
    }



class AccountConfigSettings(orm.TransientModel):
    _inherit = 'account.config.settings'

    _columns = {
        'e_invoice_user_id': fields.related('company_id', 'e_invoice_user_id',
            type='many2one', relation='res.users',
            string='Supplier e-invoice creator',
            help="This user will be used at supplier e-invoice creation. "
                 "This setting is relevant in multi-company environments"),
    }
