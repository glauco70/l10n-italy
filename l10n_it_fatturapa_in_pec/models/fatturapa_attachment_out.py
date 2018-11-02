# -*- coding: utf-8 -*-
# Copyright 2018 Sergio Corato (https://efatto.it)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import zipfile
import logging
import os
import base64
from lxml import etree
from odoo import api, models, _
from odoo.tools import config

_logger = logging.getLogger(__name__)


class FatturaPAAttachmentOut(models.Model):
    _inherit = "fatturapa.attachment.out"

    @api.multi
    def parse_pec_attachment(self, attachment_ids):
        message_dict = super(FatturaPAAttachmentOut, self).parse_pec_response(
            message_dict)




