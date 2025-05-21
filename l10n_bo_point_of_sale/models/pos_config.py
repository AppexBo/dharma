# -*- coding:utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
class PosConfig(models.Model):
    _inherit = ['pos.config']
    
    
    enable_bo_edi = fields.Boolean(
        string='Habilitar punto de venta (BO)',
        copy=False
    )

    
    @api.onchange('enable_bo_edi')
    def _onchange_enable_bo_edi(self):
        if self.enable_bo_edi:
            branch_office_id = self.env['l10n.bo.branch.office'].search([('company_id','=',self.company_id.id)], limit=1)
            if branch_office_id:
                self.write({'branch_office_id' : branch_office_id.id})
        else:
            self.write({'branch_office_id' : False, 'pos_id' : False, 'document_type_id' : False})
    
    
    
    branch_office_id = fields.Many2one(
        string='Sucursal (BO)',
        comodel_name='l10n.bo.branch.office',
    )
    
    
    pos_id = fields.Many2one(
        string='Punto de venta (BO)',
        comodel_name='l10n.bo.pos',
        copy=False
    )
    
    
    document_type_id = fields.Many2one(
        string='Tipo documento',
        comodel_name='l10n.bo.pos.sequence',
    )

    
    @api.constrains('document_type_id')
    def _check_document_type_id(self):
        for record in self:
            if record.document_type_id:
                if record.document_type_id.name.getCode() not in [1]:
                    raise UserError(f'La implementacion de POS Odoo no esta disponible para el documento: {record.document_type_id.name.name}')
                

    def open_ui(self):
        self.validate_journal_edi()
        self.validate_payment_method()
        res = super(PosConfig, self).open_ui()
        return res
    
    def validate_payment_method(self):
        if self.enable_bo_edi:
            for payment_method_id in self.payment_method_ids:
                if not payment_method_id.payment_type_id:
                    raise UserError(f'Todos los metodos de pago para este POS deben tener un Tipo de pago (BO), PAGO: {payment_method_id.name}')
        
    def validate_journal_edi(self):
        if (self.invoice_journal_id.bo_edi and not self.enable_bo_edi) or (self.enable_bo_edi and not self.invoice_journal_id.bo_edi):
            raise UserError('Diario de facturas para punto de venta invalido')
        
        
    
    adm_edi = fields.Boolean(
        string='Adm EDI',
        compute='_compute_adm_edi' 
    )
    
    def is_enbale_user(self) -> bool:
        for record in self:
            group = record.env.ref('l10n_bo_bolivian_invoice.group_adm_invoice_edi')
            return True if group and record.env.user in group.users else False    
    
    def _compute_adm_edi(self):
        for record in self:
            record.adm_edi = record.is_enbale_user()    
    