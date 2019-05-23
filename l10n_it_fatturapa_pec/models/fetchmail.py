# -*- coding: utf-8 -*-
# Copyright 2018 Lorenzo Battistini <https://github.com/eLBati>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from datetime import datetime

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

MAX_POP_MESSAGES = 50


class Fetchmail(orm.Model):
    _inherit = 'fetchmail.server'

    def _default_e_inv_notify_partner_ids(self, cr, uid, ids, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return [(6, 0, [user.partner_id.id])]

    _columns = {
        'last_pec_error_message': fields.text(
            'Last PEC error message', readonly=True),
        'pec_error_count': fields.integer("PEC error count", readonly=True),
        'e_inv_notify_partner_ids': fields.many2many(
            "res.partner", string="Contacts to notify",
            help="Contacts to notify when PEC message can't be processed",
            domain=[('email', '!=', False)],),
    }

    _defaults = {
        'e_inv_notify_partner_ids': _default_e_inv_notify_partner_ids
    }

    def fetch_mail(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for server in self.browse(cr, uid, ids, context=context):
            if not server.is_fatturapa_pec:
                super(Fetchmail, self).fetch_mail(
                    cr, uid, [server.id], context=context)
            else:
                additional_context = {
                    'fetchmail_cron_running': True
                }
                # Setting fetchmail_cron_running to avoid to disable cron while
                # cron is running (otherwise it would be done by setting
                # server.state = 'draft',
                # see _update_cron method)
                context.update(**additional_context)
                _logger.info(
                    'start checking for new e-invoices on %s server %s',
                    server.type, server.name)
                additional_context['fetchmail_server_id'] = server.id
                additional_context['server_type'] = server.type
                imap_server = None
                pop_server = None
                error_raised = False
                mail_thread = self.pool.get('mail.thread')
                _logger.info('start checking for new emails on %s server %s',
                             server.type, server.name)
                context.update({
                        'fetchmail_server_id': server.id,
                        'server_type': server.type,
                        'fetchmail_cron_running': True,
                        })
                context.update(**additional_context)
                imap_server = None
                pop_server = None
                if server.type == 'imap':
                    try:
                        imap_server = server.connect()
                        imap_server.select()
                        result, data = imap_server.search(None, '(UNSEEN)')
                        for num in data[0].split():
                            result, data = imap_server.fetch(num, '(RFC822)')
                            imap_server.store(num, '-FLAGS', '\\Seen')
                            try:
                                mail_thread.message_process(
                                    cr, uid, server.object_id.model,
                                    data[0][1],
                                    save_original=server.original,
                                    strip_attachments=(not server.attach),
                                    context=context)
                                # if message is processed without exceptions
                                server.write({'last_pec_error_message': ''})
                            except Exception as e:
                                _logger.info(
                                    'Failed to process mail from %s server %s.'
                                    ' Resetting server status',
                                    server.type, server.name, exc_info=True)
                                # Here is where we need to intervene.
                                # Setting to draft prevents new e-invoices to
                                # be sent via PEC
                                server.last_pec_error_message = str(e)
                                error_raised = True
                                continue
                            imap_server.store(num, '+FLAGS', '\\Seen')
                            # We need to commit because message is processed:
                            # Possible next exceptions, out of try, should not
                            # rollback processed messages
                            cr.commit()
                    except Exception as e:
                        _logger.info(
                            "General failure when trying to fetch mail from %s"
                            " server %s.",
                            server.type, server.name, exc_info=True)
                        server.write({
                            'last_pec_error_message': str(e),
                        })
                        error_raised = True
                    finally:
                        if imap_server:
                            imap_server.close()
                            imap_server.logout()
                elif server.type == 'pop':
                    try:
                        while True:
                            pop_server = server.connect()
                            (num_messages, total_size) = pop_server.stat()
                            pop_server.list()
                            for num in range(
                                    1, min(MAX_POP_MESSAGES, num_messages) + 1
                            ):
                                (header, messages, octets) = pop_server.retr(
                                    num)
                                message = '\n'.join(messages)
                                try:
                                    mail_thread.message_process(
                                        cr, uid, server.object_id.model,
                                        message,
                                        save_original=server.original,
                                        strip_attachments=(not server.attach),
                                        context=context)
                                    pop_server.dele(num)
                                    # See the comments in the IMAP part
                                    server.write(
                                        {'last_pec_error_message': ''})
                                except Exception as e:
                                    _logger.info(
                                        'Failed to process mail from %s server'
                                        ' %s. Resetting server status',
                                        server.type, server.name, exc_info=True
                                    )
                                    # See the comments in the IMAP part
                                    server.write({
                                        'last_pec_error_message': str(e),
                                    })
                                    error_raised = True
                                    continue
                                cr.commit()
                            if num_messages < MAX_POP_MESSAGES:
                                break
                            pop_server.quit()
                    except Exception as e:
                        _logger.info(
                            "General failure when trying to fetch mail from %s"
                            " server %s.",
                            server.type, server.name, exc_info=True)
                        # See the comments in the IMAP part
                        server.write({
                            'last_pec_error_message': str(e),
                        })
                        error_raised = True
                    finally:
                        if pop_server:
                            pop_server.quit()
                server.write({'date': datetime.now().strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)})
                if error_raised:
                    server.pec_error_count += 1
                    max_retry = self.pool['ir.config_parameter'].get_param(
                        'fetchmail.pec.max.retry')
                    if server.pec_error_count > int(max_retry):
                        # Setting to draft prevents new e-invoices to
                        # be sent via PEC.
                        # Resetting server state only after N fails.
                        # So that the system can try to fetch again after
                        # temporary connection errors
                        server.write({
                            'state': 'draft',
                        })
                        server.notify_about_server_reset(cr, uid, ids, context)
                else:
                    server.write({
                        'pec_error_count': 0
                    })
            server.write({'date': datetime.now().strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)})
        return True

    def notify_about_server_reset(self, cr, uid, ids, context):
        if self.e_inv_notify_partner_ids:
            self.pool['mail.mail'].create(cr, uid, {
                'subject': _(
                    "Fetchmail PEC server [%s] reset"
                ) % self.name,
                'body_html': _(
                    "<p>"
                    "PEC server %s has been reset. Last error message is</p>"
                    "<p><strong>%s</strong></p>"
                ) % (self.name, self.last_pec_error_message),
                'recipient_ids': [(
                    6, 0,
                    self.e_inv_notify_partner_ids.ids
                )]
            })
            _logger.info(
                'Notifying partners %s about PEC server %s reset'
                % (self.e_inv_notify_partner_ids.ids, self.name)
            )
        else:
            _logger.error(
                "Can't notify anyone about PEC server %s reset" % self.name)
