# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError

class AccountMoveLine(models.Model):
    _inherit = ['account.move.line']

    def getQuantity(self, document_type_code):
        if (document_type_code in [28] and self.quantity != 1):
            raise UserError(f"La cantidad del producto servicio: {self.product_id.name} debe ser 1")
        
        if (document_type_code in [8] and self.move_id and self.move_id.pos_id and self.move_id.pos_id.zero_rate_type == 'transportation') and self.quantity != 1:
                raise UserError(f"La cantidad del producto servicio: {self.product_id.name} debe ser 1")
        
        return round(self.quantity, 2)
    

    def getPriceUnit(self):
        if self.move_id.document_type_id.getCode() not in [28, 3, 4]:
            return round( (self.price_unit * (1/self.currency_rate))  , 2)
        return self.price_unit
    
    def getSubTotal(self):
        return round( (self.quantity * self.getPriceUnit() ) - self.getAmountDiscount() , 2)
    
    def getSpeciality(self):
        if self.product_id.categ_id:
            return self.product_id.categ_id.name
        return False
    
    room_number = fields.Integer(
        string='Nro. Quirofano/sala',
    )

    def getRoomNumber(self):
        return self.room_number
    
    def getSpecialityDoctor(self):
        speciality = False
        if self.doctor_id and self.doctor_id.category_id:
            speciality = ''
            for category_id in self.doctor_id.category_id:
                speciality += category_id.name + ','
            speciality = speciality[:-1]
        return speciality
    
    # Agregar a la vista tree
    doctor_id = fields.Many2one(
        string='Médico',
        comodel_name='res.partner',
        ondelete='restrict',
    )

    def getDoctorName(self):
        if self.doctor_id:
            return self.doctor_id.name
        raise UserError('Necesita un médico en la linea de producto')
    
    def getDoctorNITCODE(self):
        if self.doctor_id:
            if self.doctor_id.vat:
                return self.doctor_id.vat
            if self.doctor_id.code:
                return self.doctor_id.code
            raise UserError('El medico necesita un NIT o un Codigo')
        raise UserError('Necesita un médico en la linea de producto')
    
    def getTuition(self):
        if self.doctor_id:
            if self.doctor_id.ref:
                return self.doctor_id.ref
        return False
            

    
    doctor_bill_number = fields.Integer(
        string='Nro. factura medico',
    )
    
    def getIceBrand(self):
        return self.product_id.getIceBrand()
    
    def getAmountIva(self, decimal = 2) -> float:
        #base = self.quantity * self.getPriceUnit()
        base = self.getSubTotal()
        #if self.move_id.document_type_id.getCode() in [14]:
        #    base -= self.getCalculateIce()
        amount_iva = base * 0.13
        return round(amount_iva, decimal)
    
    def getAmountIce(self):
        base = self.getSubTotal()
        return round(base - self.getAmountIva(), 5)
    
    def getSpecificAliquot(self):
        value = 0
        if self.getIceBrand() == 1:
            value = self.product_id.get_ice_fixed_rate()
        return round(value, 2)
    
    def getPercentageAliquot(self):
        value = 0
        if self.getIceBrand() == 1:
            value = self.product_id.get_ice_percentage_rate() / 100
        return round(value, 2)
    
    def getIceRatio(self):
        return self.product_id.getIceRatio()
    
    def getProductRatio(self):
        ratio = self.product_uom_id.ratio
        if ratio <= 0:
            raise UserError(f'No se pudo calcular la cantidad o contenido neto del producto: {self.product_id.name}')
        return ratio
    
    def getSpecificIce(self)->float:
        #amount = (self.getSpecificAliquot() * self.getProductRatio()) / 1000 # /1000ml
        amount = 0 
        if self.getIceBrand() == 1:
            amount = ((self.getSpecificAliquot() * self.getProductRatio())/ self.getIceRatio() ) * self.quantity
            #amount = self.roundingUpDecimal(amount)
        #raise UserError((self.getSpecificAliquot() * self.getProductRatio()) * self.quantity)
        return round(amount ,5)
    
    def getPercentageIce(self) -> float:
        percentaje_value = 0 
        if self.getIceBrand() == 1:
            percentaje_value = self.getPercentageAliquot() * self.getAmountIce()
        return round(percentaje_value ,5)
    

    def getQuantityIce(self):
        base = 0
        if self.getIceBrand() == 1:
            base = (self.getProductRatio() / self.getIceRatio()) * self.quantity
        return round(base,2)
    
    def getSubtotalCalculateIce(self):
        return round(self.getSubTotal() + self.getSpecificIce() + self.getPercentageIce(), 5)