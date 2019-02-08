# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from openerp import models
from openerp.addons.l10n_it_fatturapa.bindings.fatturapa_v_1_2 import (
    AltriDatiGestionaliType
)


class WizardExportFatturapa(models.TransientModel):
    _inherit = "wizard.export.fatturapa"

    def setDettaglioLinee(self, invoice, body):
        res = super(WizardExportFatturapa, self).setDettaglioLinee(
            invoice, body)
        generic_mngt_line = False
        generic_mngt_lines = invoice.related_mngt_data_ids.filtered(
            lambda x: not x.lineRef or not x.invoice_line_id and x.invoice_id)
        if generic_mngt_lines:
            generic_mngt_line = generic_mngt_lines[0]
        for DettaglioLinea in body.DatiBeniServizi.DettaglioLinee:
            dati_gestionali = AltriDatiGestionaliType()
            # get related mgnt_line if exists
            mngt_lines = filter(
                lambda x: x.lineRef == DettaglioLinea.NumeroLinea,
                invoice.related_mngt_data_ids)
            if mngt_lines:
                mngt_line = mngt_lines[0]
                if mngt_line.name:
                    dati_gestionali.TipoDato=mngt_line.name
                if mngt_line.text_ref:
                    dati_gestionali.RiferimentoTesto=mngt_line.text_ref
                if mngt_line.number_ref:
                    dati_gestionali.RiferimentoNumero=mngt_line.number_ref
                if mngt_line.date_ref:
                    dati_gestionali.RiferimentoData=mngt_line.date_ref
                DettaglioLinea.AltriDatiGestionali.append(
                    dati_gestionali
                )
            else:
                if generic_mngt_line:
                    # if fatturapa line is not referred, and exist a
                    # generic_mngt_line, add this generic mngt data to line
                    if generic_mngt_line.name:
                        dati_gestionali.TipoDato = generic_mngt_line.name
                    if generic_mngt_line.text_ref:
                        dati_gestionali.RiferimentoTesto = generic_mngt_line.\
                            text_ref
                    if generic_mngt_line.number_ref:
                        dati_gestionali.RiferimentoNumero = generic_mngt_line.\
                            number_ref
                    if generic_mngt_line.date_ref:
                        dati_gestionali.RiferimentoData = generic_mngt_line.\
                            date_ref
                    DettaglioLinea.AltriDatiGestionali.append(
                        dati_gestionali
                    )
        return res
