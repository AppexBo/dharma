# -*- coding:utf-8 -*-

from odoo import api, models, fields

import logging
_logger = logging.getLogger(__name__)



class AccountMoveSend(models.TransientModel):
    _inherit = ['account.move.send']    

    @api.model
    def _prepare_invoice_pdf_report(self, invoice, invoice_data):
        origin_pos = True
        for inv in invoice:
            if not inv.is_pos_bo():
                origin_pos = False
                break
        if not origin_pos:
            return super(AccountMoveSend, self)._prepare_invoice_pdf_report(invoice, invoice_data)
        else:
            if invoice.invoice_pdf_report_id:
                return

            content, _report_format = self.env['ir.actions.report']._render(f'l10n_bo_bolivian_invoice.ir_actions_report_invoice_bo_{invoice[0].pos_id.paper_format_type}', invoice.ids)

            invoice_data['pdf_attachment_values'] = {
                'raw': content,
                'name': invoice._get_invoice_report_filename(),
                'mimetype': 'application/pdf',
                'res_model': invoice._name,
                'res_id': invoice.id,
                'res_field': 'invoice_pdf_report_file', # Binary field
            }
        #