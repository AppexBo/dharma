# -*- coding:utf-8 -*-

from odoo import api, models, fields

class AccountMove(models.Model):
    _name = "account.move"

    def delete_standard_sale_line(self):
        for record in self:
            standard_sale_line = record.env['l10n.bo.standard.sale.line'].search([('invoice_id','=', record.id)], limit=1)
            if standard_sale_line:
                standard_sale_line.unlink()
        
    def unlink(self):
        for record in self:
            record.delete_standard_sale_line()
        result = super(AccountMove, self).unlink()
        return result
    
    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        for record in self:
            record.delete_standard_sale_line()
        return res