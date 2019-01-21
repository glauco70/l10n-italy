# -*- coding: utf-8 -*-

import os
import openerp
import tempfile
import subprocess

from contextlib import closing
from openerp.addons.web import http as openerpweb

def fix_session(req):
    cookie = req.httprequest.cookies.get("instance0|session_id")
    session_id = cookie.replace("%22","")
    req.session = req.httpsession.get(session_id)

def html_to_pdf(html):
    html_tmp_file_fd, html_tmp_file_path = tempfile.mkstemp(suffix='.html')
    with closing(os.fdopen(html_tmp_file_fd, 'wb')) as html_tmp_file:
        html_tmp_file.write(html)
    pdf_tmp_file_fd, pdf_tmp_file_path = tempfile.mkstemp(suffix='.pdf', prefix='report.tmp.')
    os.close(pdf_tmp_file_fd)
    c = ["wkhtmltopdf", html_tmp_file_path, pdf_tmp_file_path]
    subprocess.call(c)
    with open(pdf_tmp_file_path, 'rb') as pdf_file:
        return pdf_file.read()

class FatturaElettronicaController(openerpweb.Controller):
    _cp_path = "/fatturapa"

    @openerpweb.httprequest
    def preview(self, req, attachment_id, **kw):
        try:
            fix_session(req)
            html = req.session.model('ir.attachment').get_fattura_elettronica_preview([int(attachment_id)])
            pdf = html_to_pdf(html)
            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf))
            ]
            return req.make_response(pdf, headers=pdfhttpheaders)
        except:
            return req.not_found()