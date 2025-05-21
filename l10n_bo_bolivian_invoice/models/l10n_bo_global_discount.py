# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class GlobalDiscount(models.TransientModel):
    _name = 'global.discount'
    _description ="Descuento global"

    
    name = fields.Char(
        string='name',
    )
    
    
    account_move_id = fields.Many2one(
        string='Factura',
        comodel_name='account.move',
    )


    
    discount_type = fields.Selection(
        string='Tipo descuento',
        selection=[('discount', 'Descuento global'), ('giftcard', 'Gift card')],
        default='discount',
        required=True
    )

    is_gift_card = fields.Boolean(
        string='is_gift_card',
        related='account_move_id.is_gift_card',
        readonly=True,
        store=True
    )
    
    

    
    type = fields.Selection(
        string='Tipo',
        selection=[('amount', 'Monto'), ('percentage', 'Porcetaje')],
        default='amount'
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
                if record.discount_type == 'discount':
                    amount = (record.account_move_id.getAmountTotal() + record.account_move_id.amount_discount )  * (record.percentage / 100)
                    self.write({'amount': amount})
                elif record.discount_type == 'giftcard':
                    amount = (record.account_move_id.getAmountTotal() + record.account_move_id.getAmountGiftCard() + record.account_move_id.amount_discount )  * (record.percentage / 100)
                    self.write({'amount': amount})
                    
            
    

    def discounting(self):
        if self.account_move_id:
            if self.discount_type == 'discount':
                self.account_move_id.write({'amount_discount' : self.amount})
                discount_line = self.account_move_id.invoice_line_ids.filtered(lambda l: l.product_id.global_discount)
                if discount_line:
                    discount_line[0].write(
                        {
                            'price_unit' : -abs(self.amount)
                        }
                    )
                else:
                    product_disc = self.env['product.product'].search([('global_discount', '=', True)], limit=1)
                    if product_disc:
                        self.account_move_id.write(
                            {
                                'invoice_line_ids': [
                                    (
                                        0, 0, {
                                            'product_id': product_disc.id,
                                            'price_unit': -abs(self.amount),
                                            'quantity': 1
                                        }
                                    )]
                            }
                        )
                    else:
                        raise UserError('Configure su producto de descuento global')
            elif self.discount_type == 'giftcard':
                if self.account_move_id.document_type_id.name.getCode() not in [3,28]:
                    self.account_move_id.write({'amount_giftcard' : self.amount})
                    discount_line = self.account_move_id.invoice_line_ids.filtered(lambda l: l.product_id.gift_card_product)
                    if discount_line:
                        discount_line[0].write(
                            {
                                'price_unit' : -abs(self.amount)
                            }
                        )
                    else:
                        product_disc = self.env['product.product'].search([('gift_card_product', '=', True)], limit=1)
                        if product_disc:
                            self.account_move_id.write(
                                {
                                    'invoice_line_ids': [
                                        (
                                            0, 0, {
                                                'product_id': product_disc.id,
                                                'price_unit': -abs(self.amount),
                                                'quantity': 1
                                            }
                                        )]
                                }
                            )
                        else:
                            raise UserError('Cree y configure su producto Gift card')
                else:
                    raise UserError(f'El pago con gifcard no es valido para el documento: {self.account_move_id.document_type_id.name.name}')
                
            
    
    


class AccountMove(models.Model):
    _inherit = ['account.move']
    
    amount_discount = fields.Float(
        string='Monto descuento',
        copy=False,
        readonly=True 
    )
    
    
    def global_discount_wizard(self):
        return {
            'name': 'Descuento global',
            'type': 'ir.actions.act_window',
            'res_model': 'global.discount',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': "Descuento",
                'default_account_move_id': self.id
            }
        }

    def getAmountDiscount(self):
        ld = self.invoice_line_ids.filtered(lambda l: l.product_id.global_discount and l.product_id.gif_product)
        amount = 0
        if not ld:
            self.write({'amount_discount' : 0.0})
        elif ld:
            for l in ld:
                amount += l.quantity * l.price_unit
            #self.write({'amount_discount' : ld[0].price_unit * -1})
        #amount = self.amount_discount
        amount *= -1
        self.write({'amount_discount' : amount})
        if self.document_type_id.getCode() not in [28]:
            amount*= self.currency_id.getExchangeRate()
        return round(amount, 2)
    

    
    @api.constrains('invoice_line_ids')
    def _check_invoice_line_ids(self):
        for record in self:
            if record.edi_bo_invoice:
                ld = self.invoice_line_ids.filtered(lambda l: l.product_id.gift_card_product)
                if ld:
                    payment_type_id = record.env['l10n.bo.type.payment'].search([('codigoClasificador','=',35)], limit=1)
                    if payment_type_id:
                            if not record.payment_type_id or record.payment_type_id.getCode() == 1:
                                record.write({'payment_type_id': payment_type_id.id})
                                    
                            record._compute_is_gift_card()
                            record.getAmountGiftCard()
                
                record.getAmountDiscount()
                

    