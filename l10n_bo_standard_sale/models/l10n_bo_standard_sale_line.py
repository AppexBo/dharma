# -*- coding:utf-8 -*-

from odoo import api, models, fields

class L10nBoStandardSaleLine(models.Model):
    _name = 'l10n.bo.standard.sale.line'
    _description = 'Linea de registro de ventas estandar (BO)'

    
    invoice_id = fields.Many2one(
        string='Factura',
        comodel_name='account.move',
        readonly=True 
    )

    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company,
        readonly=True
    )

    
    name = fields.Integer(
        string='Nº',
        copy=False,
        readonly=True,
        index=True, 
        unique=True
    )
    
    specification = fields.Integer(
        string='ESPECIFICACION',
        copy=False,
        readonly=True,
        default=2        
    )

    
    invoice_date = fields.Date(
        string='FECHA DE LA FACTURA',
        readonly=True,
        copy=False
    )
    
    
    invoice_number = fields.Integer(
        string='N° DE LA FACTURA',
        readonly=True,
        copy=False
    )
    
    
    autorization_code = fields.Char(
        string='CODIGO DE AUTORIZACION',
        readonly=True,
        copy=False
    )
    
    
    nit_ci = fields.Char(
        string='NIT / CI CLIENTE',
        readonly=True,
        copy=False
    )
    
    
    complement = fields.Char(
        string='COMPLEMENTO',
        readonly=True,
        copy=False
    )
    
    
    reazon_social = fields.Char(
        string='NOMBRE O RAZON SOCIAL',
        readonly=True,
        copy=False
    )
    
    
    amount_total = fields.Float(
        string='IMPORTE TOTAL DE LA VENTA',
        readonly=True,
        copy=False
    )
    
    
    amount_ice = fields.Float(
        string='IMPORTE ICE',
        readonly=True,
        copy=False
    )

    
    amount_iehd = fields.Float(
        string='IMPORTE IEHD',
        readonly=True,
        copy=False
    )
    
    
    amount_ipj = fields.Float(
        string='IMPORTE IPJ',
        readonly=True,
        copy=False
    )
    
    
    amount_rate = fields.Float(
        string='TASAS',
        readonly=True,
        copy=False
    )
    
    
    amount_no_iva = fields.Float(
        string='OTROS NO SUJETOS AL IVA',
        readonly=True,
        copy=False
    )

    
    amount_exempt = fields.Float(
        string='EXPORTACIONES Y OPERACIONES EXENTAS',
        readonly=True,
        copy=False
    )
    
    
    amount_cero_rate = fields.Float(
        string='VENTAS GRAVADAS A TASA CERO',
        readonly=True,
        copy=False
    )
    
    
    amount_subtotal = fields.Float(
        string='SUBTOTAL',
        compute='_compute_amount_subtotal' 
    )
    
    @api.depends('amount_total','amount_ice','amount_iehd','amount_ipj','amount_rate','amount_no_iva','amount_exempt','amount_cero_rate')
    def _compute_amount_subtotal(self):
        for record in self:
            amount = record.amount_total - record.amount_ice - record.amount_iehd - record.amount_ipj - record.amount_rate - record.amount_no_iva - record.amount_exempt - record.amount_cero_rate
            record.amount_subtotal = round(amount, 2)
    
    amount_discount = fields.Float(
        string='DESCUENTOS, BONIFICACIONES Y REBAJAS SUJETAS AL IVA',
        readonly=True,
        copy=False
    )
    
    
    amount_gift_card = fields.Float(
        string='IMPORTE GIFT CARD',
        readonly=True,
        copy=False
    )
    
    
    amount_fiscal_debit_base = fields.Float(
        string='IMPORTE BASE PARA DEBITO FISCAL',
        compute='_compute_amount_fiscal_debit_base' 
    )
    
    @api.depends('amount_subtotal','amount_discount','amount_gift_card')
    def _compute_amount_fiscal_debit_base(self):
        for record in self:
            amount = record.amount_subtotal - record.amount_discount - record.amount_gift_card
            record.amount_fiscal_debit_base = round(amount, 2)
    
    
    
    
    
    amount_fiscal_debit = fields.Float(
        string='DEBITO FISCAL',
        compute='_compute_amount_fiscal_debit' 
    )
    
    @api.depends('amount_fiscal_debit_base')
    def _compute_amount_fiscal_debit(self):
        for record in self:
            amount = record.amount_fiscal_debit_base * 0.13
            record.amount_fiscal_debit =  round(amount, 2)
    
    
    
    
    state = fields.Char(
        string='ESTADO',
        readonly=True,
        copy=False
    )
    
    control_code = fields.Char(
        string='CODIGO DE CONTROL',
        readonly=True,
        copy=False
    )

    
    register_type = fields.Char(
        string='TIPO DE VENTA',
        readonly=True,
        copy=False
    )
    
    @api.model
    def showMessage(self, title = None, body = None):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': f"{title or 'MENSAJE'}",
                'message': f"{body or 'Mensaje al usuario.'}",
                'sticky': False,
            }
        }
    
    
    standard_sale_id = fields.Many2one(
        string='Venta estandar (BO)',
        comodel_name='l10n.bo.standard.sale',
        readonly=True 
    )