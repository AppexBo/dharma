#-*- coding:utf-8 -*-

from odoo import api, models, fields

class PosOrderLine(models.Model):
    _inherit = ['pos.order.line']
    
    @api.model
    def isGiftProduct(self, ID = None):
        is_gif_product = False
        if ID:
            product_id = self.env['product.product'].search([('id','=',ID)], limit=1)
            if product_id:
                is_gif_product = product_id.gif_product
        else:
            is_gif_product = self.product_id.gif_product
        return is_gif_product
    
    @api.model
    def udpate_amounts(self, MOVE_ID = None):
        self.ensure_one()
        if MOVE_ID:
            pos_order_id = self.env['pos.order'].search([('id','=',MOVE_ID)])
            for reg in pos_order_id:
                reg._onchange_amount_all()

    
    @api.model
    def create(self, values):
        UPDATE = False
        if self.isGiftProduct(values.get('product_id')):
            
            if values.get('price_unit') > 0:
                UPDATE = True
                values['price_unit'] = values.get('price_unit')*-1
            if values.get('price_subtotal') > 0:
                UPDATE = True
                values['price_subtotal'] = values.get('price_subtotal')*-1
            if values.get('price_subtotal_incl') > 0:
                UPDATE = True
                values['price_subtotal_incl'] = values.get('price_subtotal_incl')*-1
            
        result = super(PosOrderLine, self).create(values)

        return result
    