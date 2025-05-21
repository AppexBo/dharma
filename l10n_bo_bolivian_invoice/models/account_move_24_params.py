# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)



class AccountMove24Params(models.Model):    
    _inherit = ['account.move']
    
    def credit_debit_note_format(self):
        cabecera = """<cabecera>"""
        cabecera += f"""<nitEmisor>{self.company_id.getNit()}</nitEmisor>"""
        cabecera += f"""<razonSocialEmisor>{self.getCompanyName()}</razonSocialEmisor>"""
        cabecera += f"""<municipio>{self.getMunicipality()}</municipio>"""
        cabecera += f"""<telefono>{self.getPhone()}</telefono>"""
        cabecera += f"""<numeroNotaCreditoDebito>{self.invoice_number}</numeroNotaCreditoDebito>"""
        cabecera += f"""<cuf>{self.getCuf()}</cuf>"""
        cabecera += f"""<cufd>{self.getCufd()}</cufd>"""
        cabecera += f"""<codigoSucursal>{self.getBranchCode()}</codigoSucursal>"""
        cabecera += f"""<direccion>{self.getAddress()}</direccion>"""
        cabecera += f"""<codigoPuntoVenta>{self.getPosCode()}</codigoPuntoVenta>"""
        cabecera += f"""<fechaEmision>{self.getEmisionDate()}</fechaEmision>"""
        cabecera += f"""<nombreRazonSocial>{self.getNameReazonSocial()}</nombreRazonSocial>"""
        cabecera += f"""<codigoTipoDocumentoIdentidad>{self.partner_id.getIdentificationCode()}</codigoTipoDocumentoIdentidad>"""
        cabecera += f"""<numeroDocumento>{self.partner_id.getNit()}</numeroDocumento>"""
        cabecera += f"""<complemento>{self.getPartnerComplement()}</complemento>""" if self.getPartnerComplement() else """<complemento xsi:nil="true"/>"""
        cabecera += f"""<codigoCliente>{self.partner_id.vat}</codigoCliente>"""
        cabecera += f"""<numeroFactura>{self.getOriginalInvoiceNumber()}</numeroFactura>"""
        cabecera += f"""<numeroAutorizacionCuf>{self.getOriginalCuf()}</numeroAutorizacionCuf>"""
        cabecera += f"""<fechaEmisionFactura>{self.getOriginalInvoiceDate()}</fechaEmisionFactura>"""
        cabecera += f"""<montoTotalOriginal>{self.getOriginalAmountOnIva()}</montoTotalOriginal>"""
        cabecera += f"""<montoTotalDevuelto>{self.getAmountTotal()}</montoTotalDevuelto>"""
        cabecera += f"""<montoDescuentoCreditoDebito>{self.getAmountDiscount()}</montoDescuentoCreditoDebito>""" if self.amount_discount > 0 else """<montoDescuentoCreditoDebito xsi:nil="true"/>"""
        cabecera += f"""<montoEfectivoCreditoDebito>{self.getAmountEffective()}</montoEfectivoCreditoDebito>"""
        cabecera += f"""<codigoExcepcion>{1 if self.force_send else 0}</codigoExcepcion>"""
        cabecera += f"""<leyenda>{self.getLegend()}</leyenda>"""
        cabecera += f"""<usuario>{self.user_id.name}</usuario>"""
        cabecera += f"""<codigoDocumentoSector>{self.getDocumentSector()}</codigoDocumentoSector>"""
        cabecera += """</cabecera>"""
        
        detalle  = """"""
        
        
        for line in self.reversed_entry_id.invoice_line_ids:
            if line.display_type == 'product' and not line.product_id.gif_product:
                detalle  += """<detalle>"""
                detalle += f"""<actividadEconomica>{line.product_id.getAe()}</actividadEconomica>"""
                detalle += f"""<codigoProductoSin>{line.product_id.getServiceCode()}</codigoProductoSin>"""
                detalle += f"""<codigoProducto>{line.product_id.getCode()}</codigoProducto>"""
                detalle += f"""<descripcion>{line.product_id.name}</descripcion>"""
                
                
                detalle += f"""<cantidad>{round(line.quantity,2)}</cantidad>"""
                detalle += f"""<unidadMedida>{line.product_uom_id.getCode()}</unidadMedida>"""
                detalle += f"""<precioUnitario>{line.getPriceUnit()}</precioUnitario>"""
                detalle += f"""<montoDescuento>{line.prorated_line_discount}</montoDescuento>""" if line.prorated_line_discount > 0 else """<montoDescuento xsi:nil="true"/>"""
                detalle += f"""<subTotal>{line.getSubTotal()}</subTotal>"""
                detalle += f"""<codigoDetalleTransaccion>1</codigoDetalleTransaccion>"""
                detalle += """</detalle>"""
        
        
        for line in self.invoice_line_ids:
            if line.display_type == 'product' and not line.product_id.gif_product:
                detalle  += """<detalle>"""
                detalle += f"""<actividadEconomica>{line.product_id.getAe()}</actividadEconomica>"""
                detalle += f"""<codigoProductoSin>{line.product_id.getServiceCode()}</codigoProductoSin>"""
                detalle += f"""<codigoProducto>{line.product_id.getCode()}</codigoProducto>"""
                detalle += f"""<descripcion>{line.name}</descripcion>"""
                detalle += f"""<cantidad>{round(line.quantity,2)}</cantidad>"""
                detalle += f"""<unidadMedida>{line.product_uom_id.getCode()}</unidadMedida>"""
                detalle += f"""<precioUnitario>{line.getPriceUnit()}</precioUnitario>"""
                detalle += f"""<montoDescuento>{line.getAmountDiscount()}</montoDescuento>""" if line.getAmountDiscount() > 0 else """<montoDescuento xsi:nil="true"/>"""
                detalle += f"""<subTotal>{line.getSubTotal()}</subTotal>"""
                detalle += f"""<codigoDetalleTransaccion>2</codigoDetalleTransaccion>"""
                detalle += """</detalle>"""
        return cabecera + detalle

    def credit_debit_note_format_computerized(self):
        _format = f"""<notaFiscalComputarizadaCreditoDebito xsi:noNamespaceSchemaLocation="notaComputarizadaCreditoDebito.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">"""
        _format += self.credit_debit_note_format()
        _format += f"""</notaFiscalComputarizadaCreditoDebito>"""
        return _format
    

    def credit_debit_note_format_electronic(self):
        _format = f"""<notaFiscalElectronicaCreditoDebito xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="/creditoDebito/notaElectronicaCreditoDebito.xsd">"""
        _format += self.credit_debit_note_format()
        _format += f"""</notaFiscalElectronicaCreditoDebito>"""
        return _format
    


    def getOriginalInvoiceNumber(self):
        for record in self:
            if record.reversed_entry_id:
                if record.reversed_entry_id.edi_bo_invoice:
                    return record.reversed_entry_id.invoice_number
                else:
                    raise UserError('La factura revertiva no es una factura fiscal.')
            else:
                raise UserError('No tiene una factura de origen')
    
    def getOriginalCuf(self):
        for record in self:
            return record.reversed_entry_id.cuf
        
    
    def getOriginalInvoiceDate(self):
        for record in self:
            return record.reversed_entry_id.getEmisionDate()
        
    def getOriginalAmountOnIva(self):
        for record in self:
            return record.reversed_entry_id.getAmountOnIva()
        
    def getAmountEffective(self):
        for record in self:
            return round(record.getAmountOnIva() * 0.13, 2)