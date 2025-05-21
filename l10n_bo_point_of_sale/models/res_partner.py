# -*- coding:utf-8 -*-

from odoo import api, models, fields

class ResPartner(models.Model):
    _inherit = ['res.partner']
    
    
    exception = fields.Boolean(
        string='Forzar NIT',
        copy=False
    )
    
    
    