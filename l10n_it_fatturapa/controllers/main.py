# -*- coding: utf-8 -*-

import os
import tempfile
import subprocess
import logging

from contextlib import closing
from openerp.addons.web import http as openerpweb

logger = logging.getLogger('FatturaPAController')


def which(file_name):
    for path in os.environ.get('PATH', os.defpath).split(os.pathsep):
        if os.path.exists(os.path.join(path, file_name)):
            return os.path.join(path, file_name)
    return False


def fix_session(req):
    cookie = req.httprequest.cookies.get("instance0|session_id")
    session_id = cookie.replace("%22","")
    req.session = req.httpsession.get(session_id)


def html_to_pdf(html):
    data = ''

    html_tmp_file_fd, html_tmp_file_path = tempfile.mkstemp(
        suffix='.html', prefix='fatturapa.')
    with closing(os.fdopen(html_tmp_file_fd, 'wb')) as html_tmp_file:
        html_tmp_file.write(html)

    pdf_tmp_file_fd, pdf_tmp_file_path = tempfile.mkstemp(
        suffix='.pdf', prefix='fatturapa.')
    os.close(pdf_tmp_file_fd)

    executable = which("wkhtmltopdf")
    if executable:
        process = subprocess.Popen(
            [executable, html_tmp_file_path, pdf_tmp_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        out, err = process.communicate()
        if process.returncode not in [0, 1]:
            logger.error('Error generating pdf: %s' % err)
        else:
            with open(pdf_tmp_file_path, 'rb') as pdf_file:
                data = pdf_file.read()
    else:
        logger.error('Error trying to find wkhtmltopdf executable!')

    try:
        os.unlink(html_tmp_file_path)
    except (OSError, IOError):
        logger.error('Error trying to remove file %s' % html_tmp_file_path)

    try:
        os.unlink(pdf_tmp_file_path)
    except (OSError, IOError):
        logger.error('Error trying to remove file %s' % pdf_tmp_file_path)

    return data


class FatturaElettronicaController(openerpweb.Controller):
    _cp_path = "/fatturapa"

    @openerpweb.httprequest
    def preview(self, req, attachment_id, **kw):
        try:
            fix_session(req)
            a = req.session.model('ir.attachment')
            html = a.get_fattura_elettronica_preview([int(attachment_id)])
            pdf = html_to_pdf(html)
            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf))
            ]
            return req.make_response(pdf, headers=pdfhttpheaders)
        except:
            logger.exception('preview failed')
            return req.not_found()
