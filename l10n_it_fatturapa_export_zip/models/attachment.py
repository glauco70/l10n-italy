# -*- coding: utf-8 -*-

from openerp import models, fields


class FatturaAttachmentOut(models.Model):
    _inherit = ['fatturapa.attachment.out']

    exported = fields.Boolean('Zip Exported')


class FatturaAttachmentIn(models.Model):
    _inherit = ['fatturapa.attachment.in']

    exported = fields.Boolean('Zip Exported')
