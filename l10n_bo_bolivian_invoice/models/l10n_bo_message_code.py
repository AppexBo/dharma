# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class messageList(models.Model):
    _name = "message.code"
    _description = "Codigo de mensaje"

    
    
    name = fields.Datetime(
        string='Fecha',
        default=fields.Datetime.now,
        copy=False
        
    )
    
    
    
    
    code = fields.Integer(
        string='Codigo',
        copy=False
        
    )
    
    
    
    
    description = fields.Text(
        string='Descripción',
        copy=False
        
    )

    
    account_move_id = fields.Many2one(
        string='Factura',
        comodel_name='account.move',
        copy=False
    )
    