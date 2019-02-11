# -*- coding: utf-8 -*-

from openerp.osv import orm, fields


class FatturaAttachmentOut(orm.Model):
    _inherit = 'fatturapa.attachment.out'

    _columns = {
        'zip_exported': fields.boolean('Zip Exported'),
    }


class FatturaAttachmentIn(orm.Model):
    _inherit = 'fatturapa.attachment.in'

    _columns = {
        'zip_exported': fields.boolean('Zip Exported'),
    }
