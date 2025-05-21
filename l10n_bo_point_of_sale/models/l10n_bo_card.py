# -*- coding:utf-8 -*-

from odoo import api, models, fields

class L10nBoCard(models.Model):
    _name = 'l10n.bo.card'
    _description = 'Tarjeta de venta'

    
    name = fields.Char(
        string='Pedido',
        required=True
    )
    
    
    card = fields.Char(
        string='Tarjeta',
        required=True
    )
    
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )
    