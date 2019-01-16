# -*- coding: utf-8 -*-
# Author(s): Andrea Colangelo (andreacolangelo@openforce.it)
# Copyright 2018 Openforce Srls Unipersonale (www.openforce.it)
# Copyright 2018 Sergio Corato (https://efatto.it)
# Copyright 2018 Lorenzo Battistini <https://github.com/eLBati>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import re
import base64
import zipfile
import io

from openerp import api, models

_logger = logging.getLogger(__name__)

FATTURAPA_IN_REGEX = "^[A-Z]{2}[a-zA-Z0-9]{11,16}_[a-zA-Z0-9]{,5}.(xml|zip)"
RESPONSE_MAIL_REGEX = '[A-Z]{2}[a-zA-Z0-9]{11,16}_[a-zA-Z0-9]{,5}_MT_' \
                      '[a-zA-Z0-9]{,3}'


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def clean_message_dict(self, message_dict):
        del message_dict['attachments']
        del message_dict['cc']
        del message_dict['from']
        del message_dict['to']

    @api.model
    def message_route(self, message, message_dict, model=None, thread_id=None,
                      custom_values=None):

        mail_model = self.env['mail.message'].with_context(
            message_create_from_mail_mail=True)

        if any("@pec.fatturapa.it" in x for x in [
            message.get('Reply-To', ''),
            message.get('From', ''),
            message.get('Return-Path', '')]
        ):
            _logger.info("Processing FatturaPA PEC with Message-Id: "
                         "{}".format(message.get('Message-Id')))

            fatturapa_regex = re.compile(FATTURAPA_IN_REGEX)
            response_regex = re.compile(RESPONSE_MAIL_REGEX)
            fatturapa_attachments = []
            response_attachments = []
            for attachment in message_dict['attachments']:
                if fatturapa_regex.match(attachment[0]):
                    fatturapa_attachments.append(attachment)

                if response_regex.match(attachment[0]):
                    response_attachments.append(attachment)

            if response_attachments and fatturapa_attachments:
                # this is an electronic invoice
                if len(response_attachments) > 1:
                    _logger.info(
                        'More than 1 message found in mail of incoming '
                        'invoice')
                message_dict['record_name'] = message_dict['subject']
                model = 'fatturapa.attachment.in'
                res_id = 0
                attachment_m_ids = self._message_preprocess_attachments(
                    message_dict['attachments'], [], model, res_id)

                attachment_ids = [att_id for m, att_id in attachment_m_ids]
                attachments = self.env['ir.attachment'].browse(attachment_ids)
                for attachment in attachments:
                    if fatturapa_regex.match(attachment.name):
                        self.create_fatturapa_attachment_in(attachment)

                message_dict['attachment_ids'] = attachment_m_ids
                self.clean_message_dict(message_dict)

                # message_create_from_mail_mail to avoid to notify message
                # (see mail.message.create)
                mail_model.create(message_dict)
                _logger.info('Routing FatturaPA PEC E-Mail with Message-Id: {}'
                             .format(message.get('Message-Id')))
                return []

            else:
                # this is an SDI notification
                message_dict = self.env['fatturapa.attachment.out']\
                    .parse_pec_response(message_dict)
                
                message_dict['record_name'] = message_dict['subject']
                attachment_ids = self._message_preprocess_attachments(
                    message_dict['attachments'], [],
                    message_dict['model'], message_dict['res_id'])

                message_dict['attachment_ids'] = attachment_ids
                self.clean_message_dict(message_dict)

                # message_create_from_mail_mail to avoid to notify message
                # (see mail.message.create)
                mail_model.create(message_dict)
                _logger.info('Routing FatturaPA PEC E-Mail with Message-Id: {}'
                             .format(message.get('Message-Id')))
                return []

        elif self._context.get('fetchmail_server_id', False):
            fetchmail_server_id = self.env['fetchmail.server'].browse(
                self._context['fetchmail_server_id'])
            if fetchmail_server_id.is_fatturapa_pec:
                att = self.find_attachment_by_subject(message_dict['subject'])
                if att:
                    message_dict['model'] = 'fatturapa.attachment.out'
                    message_dict['res_id'] = att.id
                    self.clean_message_dict(message_dict)
                    mail_model.create(message_dict)
                else:
                    _logger.error('Can\'t route PEC E-Mail with Message-Id: {}'
                                  .format(message.get('Message-Id')))
                return []

        return super(MailThread, self).message_route(
            message, message_dict, model=model, thread_id=thread_id,
            custom_values=custom_values)

    def find_attachment_by_subject(self, subject):
        if 'CONSEGNA: ' in subject:
            att_name = subject.replace('CONSEGNA: ', '')
            fatturapa_attachment_out = self.env[
                'fatturapa.attachment.out'
            ].search([('datas_fname', '=', att_name)])
            if len(fatturapa_attachment_out) == 1:
                return fatturapa_attachment_out
        if 'ACCETTAZIONE: ' in subject:
            att_name = subject.replace('ACCETTAZIONE: ', '')
            fatturapa_attachment_out = self.env[
                'fatturapa.attachment.out'
            ].search([('datas_fname', '=', att_name)])
            if len(fatturapa_attachment_out) == 1:
                return fatturapa_attachment_out
        return False

    def create_fatturapa_attachment_in(self, attachment):
        decoded = base64.b64decode(attachment.datas)
        fatturapa_regex = re.compile(FATTURAPA_IN_REGEX)
        fatturapa_attachment_in = self.env['fatturapa.attachment.in']
        if attachment.file_type == 'application/zip':
            with zipfile.ZipFile(io.BytesIO(decoded)) as zf:
                for file_name in zf.namelist():
                    inv_file = zf.open(file_name)
                    if fatturapa_regex.match(file_name):
                        # check if this invoice is already
                        # in other fatturapa.attachment.in
                        fatturapa_atts = fatturapa_attachment_in.search([
                            ('name', '=', file_name)])
                        if fatturapa_atts:
                            _logger.info("In invoice %s already processed"
                                         % fatturapa_atts.mapped('name'))
                        else:
                            fatturapa_attachment_in.create({
                                'name': file_name,
                                'datas_fname': file_name,
                                'datas': base64.encodestring(inv_file.read())})
        else:
            fatturapa_atts = fatturapa_attachment_in.search(
                [('name', '=', attachment.name)])
            if fatturapa_atts:
                _logger.info(
                    "Invoice xml already processed in %s"
                    % fatturapa_atts.mapped('name'))
            else:
                fatturapa_attachment_in.create({
                    'ir_attachment_id': attachment.id})
