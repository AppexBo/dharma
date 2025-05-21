# -*- coding:utf-8 -*-

from odoo import api, models, fields

import logging
_logger = logging.getLogger('REPORTES:')



class IrActionsReport(models.Model):
    _inherit = ['ir.actions.report']
    

    #@api.constrains('paperformat_id')
    def _check_paperformat_id(self):
        for record in self:
            ir_action_report_id = record.env.ref('account.account_invoices')
            if ir_action_report_id and ir_action_report_id.id == record.id: 
                if record.paperformat_id and record.paperformat_id.code and record.paperformat_id.code in ['1','2']:
                    pos_ids = record.sudo().env['l10n.bo.pos'].search([])
                    for pos_id in pos_ids:
                        pos_id.write({'pos_paper_format_type' : record.paperformat_id.code})

    