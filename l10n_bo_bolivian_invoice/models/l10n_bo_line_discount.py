# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError


class LineDiscount(models.TransientModel):
    _name = 'line.discount'
    _description ="Descuento por linea"

    
    
    
    name = fields.Many2one(
        string='Linea de factura',
        comodel_name='account.move.line',
    )

    
    type = fields.Selection(
        string='Tipo',
        selection=[('amount', 'Monto'), ('percentage', 'Porcetaje')],
        default='amount',
        required=True
    )

    
    amount = fields.Float(
        string='Monto',
    )

    
    percentage = fields.Float(
        string='Porcentaje',
    )
    
    def action_done(self):
        self.discounting()
        return {'type': 'ir.actions.act_window_close'}
    
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
    
    @api.onchange('percentage')
    @api.constrains('percentage')
    def _check_percentage(self):
        for record in self:
            if record.type == 'percentage':
                amount = (record.name.quantity * record.name.price_unit)  * (record.percentage / 100)
                self.write({'amount': amount})
    

    def discounting(self):
        if self.name:
            self.name.write({'amount_discount' : self.amount})
            self.name._amount_discount()
    


class AccountMoveLineBase(models.Model):
    _inherit = ['account.move.line']
    

    amount_discount = fields.Float(
        string='Desc. Fijo',
    )

    
    fixed_discount = fields.Boolean(
        string='¿Descuento fijo?',
        readonly=True
    )

    percent_discount = fields.Boolean(
        string='¿Descuento porcentaje?',
        copy=False,
        readonly=True
    )
    
    
    #@api.onchange('amount_discount')
    #@api.constrains('amount_discount')
    def _amount_discount(self):
        for record in self:
            if record.quantity > 0 and record.price_unit > 0:
                if record.getAmountDiscount() < (record.getSubTotal() + record.getAmountDiscount()):
                    monto = record.quantity * record.price_unit
                    disc = (100 * (monto-record.amount_discount))/monto

                    #monto_formateado = "{:.10f}".format(monto)  # Aquí se especifica la precicion de decimales
                
                    record.write({'fixed_discount' : record.amount_discount>0})
                    record.write({'discount' : ( disc - 100)*-1})
                else:
                    raise UserError('El descuento no puede superar el subtotal')
            else:
                raise UserError('La cantidad y el precio deben ser mayor a cero')
                
    

    def getAmountDiscount(self):
        amount = self.amount_discount
        if self.move_id.document_type_id.getCode() not in [28]: # /|\ ADD MORE DOCUMENTS TO RATE CONVERT  ...
            amount *= (1/self.currency_rate)
        return round(amount,2 )
    

    
    @api.onchange('discount')
    @api.constrains('discount')
    def _discount(self):
        for record in self:
            if not record.fixed_discount and record.move_id and record.move_id.create_date:
                record.write({'percent_discount' : record.discount > 0})
                record.write({'amount_discount' : ((record.quantity * record.price_unit) * (record.discount/100) ) if record.discount>0 else 0})

        
    def line_discount_wizard(self):
        if self.display_type == 'product' and not self.product_id.gif_product:
            return {
                'name': 'Descuento por linea',
                'type': 'ir.actions.act_window',
                'res_model': 'line.discount',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_name': self.id
                }
            }
        

    
    prorated_line_discount = fields.Float(
        string='Descuento total prorateado',
        help='Acumula el descuento por linea correspondiente + el descuento global prorateado',
        copy=False,
        readonly=True
    )
    
    
    
    

    def apportionment(self):
        if self.getSubTotal() > 0:
            total_venta = (self.move_id.amountCurrency() * self.move_id.currency_id.getExchangeRate()) + self.move_id.getAmountDiscount() + self.move_id.getAmountLineDiscount()
            porcentaje_descuento_prorrateado = self.move_id.getAmountDiscount() / total_venta
            apportionment = round(porcentaje_descuento_prorrateado * (self.getSubTotal() + self.getAmountDiscount() ), 2)
            apportionment += self.getAmountDiscount()
            self.write(
                {
                    'prorated_line_discount' : round(apportionment, 2)
                }
            )


    """
        1 validar asientos masivamente
        2 Crear producto giftcard
        3 Agregar codigo de recepcion y de validacion,  estado en el envio de paquetes masivos
    """

    
    

    




class AccountMove(models.Model):
    _inherit = ['account.move']
    

    def getAmountLineDiscount(sefl):
        amount = 0
        for line in sefl.invoice_line_ids:
            if not line.product_id.global_discount:
                amount += line.getAmountDiscount()
        return amount