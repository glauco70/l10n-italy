# -*- coding: utf-8 -*-

from openerp.osv import orm, fields
import base64
import io
import zipfile


class WizardAccountInvoiceExport(orm.TransientModel):
    _name = "wizard.fatturapa.export"

    _columns = {
        'data': fields.binary("File", readonly=True),
        'name': fields.char('Filename', size=32),
        'mark_as_exported': fields.boolean('Mark as exported'),
    }

    def export_zip(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        wiz = self.browse(cr, uid, ids[0])
        model = context.get('active_model', False)
        attachments = self.pool[model].browse(
                cr, uid, context.get('active_ids', []), context=context)

        fp = io.BytesIO()
        zf = zipfile.ZipFile(fp, mode="w")

        for att in attachments:
            zf.writestr(att.datas_fname, base64.b64decode(att.datas))
        zf.close()
        fp.seek(0)
        data = fp.read()
        export_report_name = 'E-Invoices XML'
        if wiz.name:
            export_report_name = wiz.name
        attach_vals = {
            'name': export_report_name + '.zip',
            'datas_fname': export_report_name + '.zip',
            'datas': base64.encodestring(data),
        }
        att_id = self.pool['ir.attachment'].create(cr, uid, attach_vals,
                                                   context=context)
        model_data_obj = self.pool['ir.model.data']
        view_rec = model_data_obj.get_object_reference(
            cr, uid, 'base', 'view_attachment_form')
        view_id = view_rec and view_rec[1] or False
        if wiz.mark_as_exported:
            for attachment in attachments:
                attachment.write({'zip_exported': True})
        return {
            'view_type': 'form',
            'name': "Export E-Invoices",
            'view_id': [view_id],
            'res_id': att_id,
            'view_mode': 'form',
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'context': context,
        }
