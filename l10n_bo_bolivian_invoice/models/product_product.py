from odoo import api, models
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)



class ProductProduct(models.Model):
    _inherit = ['product.product']

    @api.model
    def getProduct(self):
        return self.env['product.product'].sudo().with_company(self.env.company.getGrandParent().id).browse(self.id)

    def getAe(self):
        if self.siat_service_id:
            return self.siat_service_id.getAe()
        if not self.company_id and self.env.company.id != self.env.company.getGrandParent().id:
            return self.getProduct().getAe()
        raise UserError(f'No se configuro un codigo SIAT para el producto: {self.name}')
        
    
    def getCode(self):
        if self.default_code:
            return self.default_code
        if not self.company_id and self.env.company.id != self.env.company.getGrandParent().id:
            return self.getProduct().getCode()
        raise UserError(f'El producto {self.name} no tiene una referencia interna')
    
    def getServiceCode(self):
        if self.siat_service_id:
            return self.siat_service_id.getCode()
        if not self.company_id and self.env.company.id != self.env.company.getGrandParent().id:
            return self.getProduct().getServiceCode()
        raise UserError(f'El producto {self.name} no tiene un Codigo SIAT.')
    
    def getNandinaCode(self):
        if self.siat_service_nandina_id:
            return self.siat_service_nandina_id.getCode()
        if not self.company_id and self.env.company.id != self.env.company.getGrandParent().id:
            return self.getProduct().getNandinaCode()
        raise UserError(f'El producto {self.name} no tiene un Codigo nandina del SIAT.')
    

    def get_ice_fixed_rate(self):
        if self.siat_service_nandina_id:
            return self.siat_service_nandina_id.get_fixed_rate()
        if not self.company_id and self.env.company.id != self.env.company.getGrandParent().id:
            return self.getProduct().get_ice_fixed_rate()
        raise UserError(f"Producto: {self.name}, no tiene un codigo nandina")
    
    def get_ice_percentage_rate(self):
        if self.siat_service_nandina_id:
            return self.siat_service_nandina_id.get_percentage_rate()
        if not self.company_id and self.env.company.id != self.env.company.getGrandParent().id:
            return self.getProduct().get_ice_percentage_rate()
        raise UserError(f"Producto: {self.name}, no tiene un codigo nandina")
    
    def getIceBrand(self):
        if self.siat_service_nandina_id and self.siat_service_nandina_id.ratio > 0:
            return 1
        if not self.company_id and self.env.company.id != self.env.company.getGrandParent().id:
            return self.getProduct().getIceBrand()
        return 2
    
    def getIceRatio(self):
        if self.siat_service_nandina_id:
            return self.siat_service_nandina_id.ratio
        if not self.company_id and self.env.company.id != self.env.company.getGrandParent().id:
            return self.getProduct().getIceRatio()
        return 0