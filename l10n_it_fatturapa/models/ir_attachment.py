# -*- coding: utf-8 -*-

import lxml.etree as ET
import os
import shlex
import subprocess
import logging
from io import BytesIO
from openerp.osv import fields, orm
from openerp.modules.module import get_module_resource
from openerp.osv.osv import except_osv
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class Attachment(orm.Model):
    _inherit = 'ir.attachment'

    def _compute_ftpa_preview_link(self, cr, uid, ids, name, args, context=None):
        res = {}
        for att in self.browse(cr, uid, ids, context=context):
            res[att.id] = '/fatturapa/preview?attachment_id=%s' % att.id
        return res

    _columns = {
        'ftpa_preview_link': fields.function(
            _compute_ftpa_preview_link, type='char',
            string="Preview link", readonly=True,
        )
    }

    def check_file_is_pem(self, p7m_file):
        file_is_pem = True
        strcmd = (
            'openssl asn1parse  -inform PEM -in %s'
        ) % (p7m_file)
        cmd = shlex.split(strcmd)
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            proc.communicate()
            if proc.wait() != 0:
                file_is_pem = False
        except Exception as e:
            raise except_osv(_('Error' ),
                             _('An error with command "openssl asn1parse" occurred: %s') % e.args)
        return file_is_pem

    def parse_pem_2_der(self, pem_file, tmp_der_file):
        strcmd = (
            'openssl asn1parse -in %s -out %s'
        ) % (pem_file, tmp_der_file)
        cmd = shlex.split(strcmd)
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            stdoutdata, stderrdata = proc.communicate()
            if proc.wait() != 0:
                _logger.warning(stdoutdata)
                raise Exception(stderrdata)
        except Exception as e:
            raise except_osv(_('Error' ),
                             _('Parsing PEM to DER  file %s') % e.args)
        if not os.path.isfile(tmp_der_file):
            raise except_osv(_('Error' ),
                             _('ASN.1 structure is not parsable in DER'))
        return tmp_der_file

    def decrypt_to_xml(self, signed_file, xml_file):
        strcmd = (
            'openssl smime -decrypt -verify -inform'
            ' DER -in %s -noverify -out %s'
        ) % (signed_file, xml_file)
        cmd = shlex.split(strcmd)
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            stdoutdata, stderrdata = proc.communicate()
            if proc.wait() != 0:
                _logger.warning(stdoutdata)
                raise Exception(stderrdata)
        except Exception as e:
            raise except_osv(_('Error' ),
                             _('Signed Xml file %s') % e.args)
        if not os.path.isfile(xml_file):
            raise except_osv(_('Error' ),
                             _('Signed Xml file not decryptable'))
        return xml_file

    def remove_xades_sign(self, xml):
        root = ET.XML(xml)
        for elem in root.iter('*'):
            if elem.tag.find('Signature') > -1:
                elem.getparent().remove(elem)
                break
        return ET.tostring(root)

    def strip_xml_content(self, xml):
        root = ET.XML(xml)
        for elem in root.iter('*'):
            if elem.text is not None:
                elem.text = elem.text.strip()
        return ET.tostring(root)

    def get_xml_string(self, cr, uid, ids, context={}):
        fatturapa_attachment = self.browse(cr, uid, [ids], context)[0]
        # decrypt  p7m file
        if fatturapa_attachment.datas_fname.lower().endswith('.p7m'):
            temp_file_name = (
                '/tmp/%s' % fatturapa_attachment.datas_fname.lower())
            temp_der_file_name = (
                '/tmp/%s_tmp' % fatturapa_attachment.datas_fname.lower())
            with open(temp_file_name, 'w') as p7m_file:
                p7m_file.write(fatturapa_attachment.datas.decode('base64'))
            xml_file_name = os.path.splitext(temp_file_name)[0]

            # check if temp_file_name is a PEM file
            file_is_pem = self.check_file_is_pem(temp_file_name)

            # if temp_file_name is a PEM file
            # parse it in a DER file
            if file_is_pem:
                temp_file_name = self.parse_pem_2_der(
                    temp_file_name, temp_der_file_name)

            # decrypt signed DER file in XML readable
            xml_file_name = self.decrypt_to_xml(
                temp_file_name, xml_file_name)

            with open(xml_file_name, 'r') as fatt_file:
                file_content = fatt_file.read()
            xml_string = file_content
        elif fatturapa_attachment.datas_fname.lower().endswith('.xml'):
            xml_string = fatturapa_attachment.datas.decode('base64')
        xml_string = self.remove_xades_sign(xml_string)
        xml_string = self.strip_xml_content(xml_string)
        return xml_string

    def get_fattura_elettronica_preview(self):
        xsl_path = get_module_resource(
            'l10n_it_fatturapa', 'data', 'fatturaordinaria_v1.2.1.xsl')
        xslt = ET.parse(xsl_path)
        xml_string = self.get_xml_string(
            self._cr, self._uid, self._ids, self._context)
        xml_file = BytesIO(xml_string)
        dom = ET.parse(xml_file)
        transform = ET.XSLT(xslt)
        newdom = transform(dom)
        return ET.tostring(newdom, pretty_print=True)
