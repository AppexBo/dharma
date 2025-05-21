from odoo import api, models, fields
from odoo.exceptions import UserError

class ResCurrency(models.Model):
    _inherit = ['res.currency']

    enable_bo_edi = fields.Boolean(
        string='Habilitado facturacion EDI',
        compute='_compute_enable_bo_edi' ,
    )
    
    @api.depends('active')
    def _compute_enable_bo_edi(self):
        for record in self:
            record.enable_bo_edi = record.env.company.enable_bo_edi
    

    siat_currency_id = fields.Many2one(
        string='Moneda SIAT',
        comodel_name='l10n.bo.type.currency'
    )
    
    def getCode(self):
        if self.siat_currency_id:
            return self.siat_currency_id.getCode()
        else:
            raise UserError('No tiene una moneda establecida por SIAT')
    
    def getName(self):
        if self.siat_currency_id:
            return self.siat_currency_id.getName()
        else:
            raise UserError('No tiene una moneda establecida por SIAT')
        
    def getExchangeRate(self):
        if self.siat_currency_id:
            if self.siat_currency_id.getCode() == 1:
                return 1
            return round(self.inverse_rate, 2)
        raise UserError('No tiene una moneda establecida por SIAT')
        