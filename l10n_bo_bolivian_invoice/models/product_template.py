from odoo import api, models, fields

import logging
_logger = logging.getLogger(__name__)



class ProductTemplate(models.Model):
    _inherit = ['product.template']
    
    siat_service_id = fields.Many2one(
        string='Codigo SIAT',
        comodel_name='l10n.bo.product.service',
        copy=False,
        company_dependent=True,
    )

    
    siat_service_nandina_id = fields.Many2one(
        string='Codigo nandina',
        comodel_name='l10n.bo.product.service.nandina',
        copy=False,
        company_dependent=True,
    )
    
    
    global_discount = fields.Boolean(
        string='Es descuento Global',
        copy=False, 
        help='Habilitar para productos con descuento global'        
    )

    gift_card_product = fields.Boolean(
        string='Es gift card',
        copy=False, 
        help='Habilitar para productos como tarjeta de regalo'        
    )

    
    gif_product = fields.Boolean(
        string='Producto servicio',
        copy=False
    )

    
    national_cost = fields.Boolean(
        string='Es costo nacional',
        copy=False
    )

    
    international_cost = fields.Boolean(
        string='Es costo internacional',
    )
    
    

    
    @api.constrains('global_discount', 'gift_card_product')
    def _check_global_discount(self):
        for record in self:
            record.write({'gif_product' : record.global_discount or record.gift_card_product})    
    
    
    
    
    enable_bo_edi = fields.Boolean(
        string='Habilitado facturacion EDI',
        compute='_compute_enable_bo_edi' ,
    )
    
    @api.depends('detailed_type')
    def _compute_enable_bo_edi(self):
        for record in self:
            record.enable_bo_edi = record.env.company.enable_bo_edi

    
            
    
    
    

    