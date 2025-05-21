# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError

class AccountJournal(models.Model):
    _inherit = ['account.journal']
    

    
    bo_edi = fields.Boolean(
        string='Factura (BO)',
        copy=False,
        help='Activar diario para movimientos fiscales (BO)'   
    )
    
    
    enable_bo_edi = fields.Boolean(
        string='bo edi habilitado',
        related='company_id.enable_bo_edi',
        readonly=True,
        store=True
    )
    
    
    adm_journal_bo_edi = fields.Boolean(
        string='adm_journal_bo_edi',
        compute='_compute_adm_journal_bo_edi' 
    )
    
    def is_enbale_user(self) -> bool:
        for record in self:
            group = record.env.ref('l10n_bo_bolivian_invoice.group_adm_invoice_edi')
            return True if group and record.env.user in group.users else False    
    

    @api.depends('bo_edi')
    def _compute_adm_journal_bo_edi(self):
        for record in self:
            record.adm_journal_bo_edi = record.is_enbale_user()    
    
    
    @api.onchange('bo_edi')
    def _onchange_bo_edi(self):
        if not self.is_enbale_user():
            raise UserError('Necesita permisos de ADMINISTADOR (BO) para editar la configuración del diario')