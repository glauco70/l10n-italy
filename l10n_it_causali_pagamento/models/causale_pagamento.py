# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CodiceCarica(models.Model):
    _name = 'causale.pagamento'
    _description = 'Causale Pagamento'
    _rec_name = 'display_name'

    @api.constrains('code')
    def _check_code(self):
        domain = [('code', '=', self.code)]
        elements = self.search(domain)
        if len(elements) > 1:
            raise ValidationError(
                _("The element with code %s already exists") % self.code)

    @api.multi
    @api.depends('name')
    def _compute_display_name(self):
        for cau in self:
            cau.display_name = ' '.join([cau.code, cau.name[:100]])
            if len(cau.name) > 50:
                cau.display_name += '...'

    display_name = fields.Char(
        string='Name', compute='_compute_display_name')
    code = fields.Char(string='Code', size=2, required=True)
    name = fields.Char(string='Description', required=True)
