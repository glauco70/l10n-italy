# -*- coding: utf-8 -*-

from openerp import models, api, fields
from openerp.tools import config
import base64
import zipfile
import os
import tempfile


class WizardAccountInvoiceExport(models.TransientModel):
    _name = "wizard.fatturapa.export"

    data = fields.Binary("File", readonly=True)
    name = fields.Char('Filename', size=32, readonly=True)
    mark_as_exported = fields.Boolean('Mark as exported')
    state = fields.Selection((
        ('create', 'create'),
        ('get', 'get'),
    ), default='create')

    @api.multi
    def export_zip(self):
        attachments = []
        for invoice in self.env['account.invoice'].browse(
                self._context['active_ids']):
            if invoice.type in ['out_invoice', 'out_refund']:
                if invoice.fatturapa_attachment_out_id:
                    att = invoice.fatturapa_attachment_out_id
                    attachments += [att]
            else:
                if invoice.fatturapa_attachment_in_id:
                    att = invoice.fatturapa_attachment_in_id
                    attachments += [att]

        path = os.path.join(config['data_dir'], "filestore",
                            self.env.cr.dbname)
        compression = zipfile.ZIP_STORED
        temp = tempfile.mktemp(suffix='.zip')
        zf = zipfile.ZipFile(temp, mode="w")
        for attachment in attachments:
            file_name = attachment.store_fname
            zf.write(os.path.join(path, file_name),
                     attachment.name.replace('/', '_'),
                     compress_type=compression)
        zf.close()
        data = open(temp, 'rb').read()
        export_report_name = 'E-Invoices XML'
        attach_vals = {
            'name': export_report_name + '.zip',
            'datas_fname': export_report_name + '.zip',
            'datas': base64.encodestring(data),
        }
        att_id = self.env['ir.attachment'].create(attach_vals)
        model_data_obj = self.env['ir.model.data']
        view_rec = model_data_obj.get_object_reference(
            'base', 'view_attachment_form')
        view_id = view_rec and view_rec[1] or False
        if self.mark_as_exported:
            for attachment in attachments:
                attachment.exported = True
        return {
            'view_type': 'form',
            'name': "Export E-Invoices",
            'view_id': [view_id],
            'res_id': att_id.id,
            'view_mode': 'form',
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'context': self._context,
        }
