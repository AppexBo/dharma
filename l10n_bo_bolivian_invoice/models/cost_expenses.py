# -*- coding:utf-8 -*-

from odoo import models, fields

class CostExpenseNational(models.Model):
    _name = 'cost.expense.national'
    _description = 'Costo gastos nacionales (BO)'

    
    name = fields.Char(
        string='Descripción',
        required=True
    )

    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )
    

    
    currency_id = fields.Many2one(
        string='Moneda',
        comodel_name='res.currency',
        related='account_move_id.currency_id',
        readonly=True,
        store=True
    )
    

    amount = fields.Monetary(
        string="Monto", 
        currency_field='currency_id'
    )
    
    
    account_move_id = fields.Many2one(
        string='Factura',
        comodel_name='account.move',
        ondelete='restrict',
    )

    def getAmount(self) -> float:
        return self.amount
    

class CostExpenseInternational(models.Model):
    _name = 'cost.expense.international'
    _description = 'Costo gastos internacionales (BO)'

    
    name = fields.Char(
        string='Descripción',
        required=True
    )
    
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )
    

    
    currency_id = fields.Many2one(
        string='Moneda',
        comodel_name='res.currency',
        related='account_move_id.currency_id',
        readonly=True,
        store=True
    )
    

    amount = fields.Monetary(
        string="Monto", 
        currency_field='currency_id'
    )
    
    
    account_move_id = fields.Many2one(
        string='Factura',
        comodel_name='account.move',
        ondelete='restrict',
    )
    
    def getAmount(self) -> float:
        return self.amount

