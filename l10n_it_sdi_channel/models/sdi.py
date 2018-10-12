# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

SDI_CHANNELS = [
    ('pec', 'PEC'),
    ('web', 'Web service'),
    # ('sftp', 'SFTP'), # not implemented
]


class SdiChannel(models.Model):
    _name = "sdi.channel"
    _description = "SdI channel"

    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self:
        self.env['res.company']._company_default_get('sdi.channel'))
    channel_type = fields.Selection(
        string='SdI channel type', selection=SDI_CHANNELS, required=True)
    pec_server_id = fields.Many2one(
        'ir.mail_server', string='Pec mail server', required=False)
    email_from_for_fatturaPA = fields.Char(
        "Sender Email Address for FatturaPA")
    email_exchange_system = fields.Char("Exchange System Email Address")
    web_server_address = fields.Char(string='Web server address')
    web_server_login = fields.Char(string='Web server login')
    web_server_password = fields.Char(string='Web server password')
    web_server_token = fields.Char(string='Web server token')
