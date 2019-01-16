# -*- coding: utf-8 -*-

from openerp.addons.web import http as openerpweb
#Controller, route, request


class FatturaElettronicaController(openerpweb.Controller):
    _cp_path = "/fatturapa"

    @openerpweb.httprequest
    def preview(self, req, attachment_id, **kw):
        attach = req.session.model['ir.attachment'].browse(int(attachment_id))
        html = attach.get_fattura_elettronica_preview()
        pdf = req.session.model['report']._run_wkhtmltopdf(
            [], [], [[False, html]], None, None)
        pdfhttpheaders = [
            # ('Content-Disposition', 'attachment; filename="%s"'
            #  % self.filename(model)),
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf))
        ]
        return req.make_response(pdf, headers=pdfhttpheaders)

    # ([
    #     '/fatturapa/preview/<attachment_id>',
    # ], type='http', auth='user', website=True)